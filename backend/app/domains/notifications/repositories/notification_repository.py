"""The only SQL in the notifications domain. Returns DTOs, never models."""

import base64
import json
import uuid
from datetime import datetime
from typing import Any, cast

from sqlalchemy import Select, and_, func, literal, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.core.db import user_transaction
from app.domains.notifications.constants import NOTIFY_CHANNEL
from app.domains.notifications.interfaces.dtos import (
    DeliveryStatusValue,
    EmailDeliveryDTO,
    MarkerValue,
    NotificationActionValue,
    NotificationDTO,
    NotificationKindValue,
    NotificationPageDTO,
    PublishedNotification,
    PublishNotification,
)
from app.domains.notifications.models import Notification, NotificationDelivery


class SqlNotificationRepository:
    """Reads and writes ``notifications`` and ``notification_deliveries``.

    Every method runs in a ``user_transaction``, so Row Level Security binds
    even when the caller is a background job on the service-role connection.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def insert_notification(
        self,
        *,
        publish: PublishNotification,
        show_popup: bool,
        email_status: DeliveryStatusValue,
        now: datetime,
    ) -> PublishedNotification | None:
        notification_id = uuid.uuid4()
        email_delivery_id = uuid.uuid4()
        async with user_transaction(self.session, publish.user_id) as scoped:
            inserted_id = await scoped.scalar(
                insert(Notification)
                .values(
                    id=notification_id,
                    user_id=publish.user_id,
                    kind=publish.kind,
                    source_id=publish.source_id,
                    target_id=publish.target_id,
                    title=publish.title,
                    detail=publish.detail,
                    marker=publish.marker,
                    occurred_at=publish.occurred_at,
                    time_zone=publish.time_zone,
                    created_at=now,
                )
                .on_conflict_do_nothing(
                    index_elements=["source_id"],
                    index_where=text("kind = 'reminder'"),
                )
                .returning(Notification.id)
            )
            if inserted_id is None:
                return None
            await scoped.execute(
                insert(NotificationDelivery).values(
                    [
                        {
                            "id": uuid.uuid4(),
                            "notification_id": notification_id,
                            "user_id": publish.user_id,
                            "channel": "popup",
                            "status": "sent" if show_popup else "skipped",
                            "attempts": 0,
                            "sent_at": now if show_popup else None,
                        },
                        {
                            "id": email_delivery_id,
                            "notification_id": notification_id,
                            "user_id": publish.user_id,
                            "channel": "email",
                            "status": email_status,
                            "attempts": 0,
                            "sent_at": None,
                        },
                    ]
                )
            )
            # AD-4. Delivered by PostgreSQL only when this transaction commits,
            # and never if it rolls back. Ids only, never the text (T6).
            await scoped.execute(
                text("SELECT pg_notify(:channel, :payload)"),
                {
                    "channel": NOTIFY_CHANNEL,
                    "payload": json.dumps(
                        {
                            "user_id": str(publish.user_id),
                            "notification_id": str(notification_id),
                        }
                    ),
                },
            )
            row = (
                await scoped.execute(
                    _select_with_popup().where(Notification.id == notification_id)
                )
            ).one()
        return PublishedNotification(
            notification=_row_to_dto(row=row),
            email_delivery_id=email_delivery_id,
            email_status=email_status,
        )

    async def get_email_status_for_source(
        self, *, user_id: uuid.UUID, source_id: uuid.UUID
    ) -> tuple[uuid.UUID, DeliveryStatusValue] | None:
        async with user_transaction(self.session, user_id) as scoped:
            row = (
                await scoped.execute(
                    select(NotificationDelivery.id, NotificationDelivery.status)
                    .join(
                        Notification,
                        Notification.id == NotificationDelivery.notification_id,
                    )
                    .where(
                        Notification.user_id == user_id,
                        Notification.source_id == source_id,
                        NotificationDelivery.channel == "email",
                    )
                )
            ).one_or_none()
        if row is None:
            return None
        return row[0], cast(DeliveryStatusValue, row[1])

    async def count_emails_since(self, *, user_id: uuid.UUID, since: datetime) -> int:
        async with user_transaction(self.session, user_id) as scoped:
            count = await scoped.scalar(
                select(func.count())
                .select_from(NotificationDelivery)
                .join(
                    Notification,
                    Notification.id == NotificationDelivery.notification_id,
                )
                .where(
                    NotificationDelivery.user_id == user_id,
                    NotificationDelivery.channel == "email",
                    NotificationDelivery.status.in_(("queued", "sent")),
                    Notification.created_at >= since,
                )
            )
        return int(count or 0)

    async def has_email_paused_since(
        self, *, user_id: uuid.UUID, since: datetime
    ) -> bool:
        async with user_transaction(self.session, user_id) as scoped:
            found = await scoped.scalar(
                select(Notification.id)
                .where(
                    Notification.user_id == user_id,
                    Notification.kind == "email_paused",
                    Notification.created_at >= since,
                )
                .limit(1)
            )
        return found is not None

    async def get_email_delivery(
        self, *, delivery_id: uuid.UUID
    ) -> EmailDeliveryDTO | None:
        # No user_transaction: the email job knows only the delivery id and
        # runs on the service-role connection (T3). It writes, below, as the
        # user the row belongs to.
        async with self.session.begin():
            row = (
                await self.session.execute(
                    select(NotificationDelivery, Notification)
                    .join(
                        Notification,
                        Notification.id == NotificationDelivery.notification_id,
                    )
                    .where(
                        NotificationDelivery.id == delivery_id,
                        NotificationDelivery.channel == "email",
                    )
                )
            ).one_or_none()
        if row is None:
            return None
        delivery = cast(NotificationDelivery, row[0])
        notification = cast(Notification, row[1])
        return EmailDeliveryDTO(
            delivery_id=delivery.id,
            user_id=delivery.user_id,
            status=cast(DeliveryStatusValue, delivery.status),
            attempts=delivery.attempts,
            title=notification.title,
            detail=notification.detail,
            marker=cast(MarkerValue, notification.marker),
            occurred_at=notification.occurred_at,
            time_zone=notification.time_zone,
            target_id=notification.target_id,
            notification_created_at=notification.created_at,
        )

    async def mark_email_sent(
        self,
        *,
        user_id: uuid.UUID,
        delivery_id: uuid.UUID,
        provider_message_id: str,
        sent_at: datetime,
    ) -> None:
        async with user_transaction(self.session, user_id) as scoped:
            await scoped.execute(
                update(NotificationDelivery)
                .where(
                    NotificationDelivery.id == delivery_id,
                    NotificationDelivery.user_id == user_id,
                )
                .values(
                    status="sent",
                    provider_message_id=provider_message_id,
                    sent_at=sent_at,
                    attempts=NotificationDelivery.attempts + 1,
                )
            )

    async def record_email_failure(
        self, *, user_id: uuid.UUID, delivery_id: uuid.UUID, is_final: bool
    ) -> int:
        values: dict[str, Any] = {"attempts": NotificationDelivery.attempts + 1}
        if is_final:
            values["status"] = "failed"
        async with user_transaction(self.session, user_id) as scoped:
            attempts = await scoped.scalar(
                update(NotificationDelivery)
                .where(
                    NotificationDelivery.id == delivery_id,
                    NotificationDelivery.user_id == user_id,
                )
                .values(**values)
                .returning(NotificationDelivery.attempts)
            )
        return int(attempts or 0)

    async def list_page(
        self, *, user_id: uuid.UUID, cursor: str | None, limit: int
    ) -> NotificationPageDTO:
        statement = (
            _select_with_popup()
            .where(Notification.user_id == user_id, Notification.deleted_at.is_(None))
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit + 1)
        )
        if cursor is not None:
            cursor_created_at, cursor_id = _decode_cursor(cursor=cursor)
            statement = statement.where(
                tuple_(Notification.created_at, Notification.id)
                < tuple_(literal(cursor_created_at), literal(cursor_id))
            )
        async with user_transaction(self.session, user_id) as scoped:
            rows = (await scoped.execute(statement)).all()
        items = [_row_to_dto(row=row) for row in rows[:limit]]
        has_more = len(rows) > limit
        next_cursor = (
            _encode_cursor(
                created_at=items[-1].created_at, notification_id=items[-1].id
            )
            if has_more
            else None
        )
        return NotificationPageDTO(items=items, next_cursor=next_cursor)

    async def count_unread(self, *, user_id: uuid.UUID) -> int:
        async with user_transaction(self.session, user_id) as scoped:
            count = await scoped.scalar(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                    Notification.deleted_at.is_(None),
                )
            )
        return int(count or 0)

    async def get(
        self, *, user_id: uuid.UUID, notification_id: uuid.UUID
    ) -> NotificationDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            row = (
                await scoped.execute(
                    _select_with_popup().where(
                        Notification.id == notification_id,
                        Notification.user_id == user_id,
                        Notification.deleted_at.is_(None),
                    )
                )
            ).one_or_none()
        return _row_to_dto(row=row) if row is not None else None

    async def mark_read(
        self, *, user_id: uuid.UUID, notification_id: uuid.UUID, now: datetime
    ) -> NotificationDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            await scoped.execute(
                update(Notification)
                .where(
                    Notification.id == notification_id,
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                    Notification.deleted_at.is_(None),
                )
                .values(read_at=now)
            )
            row = (
                await scoped.execute(
                    _select_with_popup().where(
                        Notification.id == notification_id,
                        Notification.user_id == user_id,
                        Notification.deleted_at.is_(None),
                    )
                )
            ).one_or_none()
        return _row_to_dto(row=row) if row is not None else None

    async def mark_all_read(self, *, user_id: uuid.UUID, now: datetime) -> int:
        async with user_transaction(self.session, user_id) as scoped:
            result = await scoped.execute(
                update(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.read_at.is_(None),
                    Notification.deleted_at.is_(None),
                )
                .values(read_at=now)
                .returning(Notification.id)
            )
            marked_ids = result.scalars().all()
        return len(marked_ids)

    async def record_action(
        self,
        *,
        user_id: uuid.UUID,
        source_id: uuid.UUID,
        action: NotificationActionValue,
        acted_at: datetime,
    ) -> None:
        async with user_transaction(self.session, user_id) as scoped:
            await scoped.execute(
                update(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.source_id == source_id,
                    Notification.kind == "reminder",
                    Notification.deleted_at.is_(None),
                )
                .values(
                    action=action,
                    acted_at=acted_at,
                    read_at=func.coalesce(Notification.read_at, acted_at),
                )
            )

    async def soft_delete_created_before(
        self, *, cutoff: datetime, now: datetime, limit: int
    ) -> int:
        # No user_transaction: the daily purge runs for every user at once on
        # the service-role connection, as a background job may (T3).
        batch = (
            select(Notification.id)
            .where(Notification.deleted_at.is_(None), Notification.created_at < cutoff)
            .limit(limit)
            .scalar_subquery()
        )
        async with self.session.begin():
            result = await self.session.execute(
                update(Notification)
                .where(Notification.id.in_(batch))
                .values(deleted_at=now)
                .returning(Notification.id)
            )
            stamped_ids = result.scalars().all()
        return len(stamped_ids)


def _select_with_popup() -> Select[Any]:
    """Each notification with whether its pop-up delivery was sent."""
    return select(Notification, NotificationDelivery.status).outerjoin(
        NotificationDelivery,
        and_(
            NotificationDelivery.notification_id == Notification.id,
            NotificationDelivery.channel == "popup",
        ),
    )


def _row_to_dto(*, row: Any) -> NotificationDTO:
    notification = cast(Notification, row[0])
    popup_status = cast(str | None, row[1])
    return NotificationDTO(
        id=notification.id,
        user_id=notification.user_id,
        kind=cast(NotificationKindValue, notification.kind),
        source_id=notification.source_id,
        target_id=notification.target_id,
        title=notification.title,
        detail=notification.detail,
        marker=cast(MarkerValue, notification.marker),
        occurred_at=notification.occurred_at,
        time_zone=notification.time_zone,
        created_at=notification.created_at,
        read_at=notification.read_at,
        action=cast(NotificationActionValue | None, notification.action),
        acted_at=notification.acted_at,
        show_popup=popup_status == "sent",
    )


def _encode_cursor(*, created_at: datetime, notification_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{notification_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(*, cursor: str) -> tuple[datetime, uuid.UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    created_at_text, notification_id_text = raw.split("|", 1)
    return datetime.fromisoformat(created_at_text), uuid.UUID(notification_id_text)
