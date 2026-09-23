"""The notification list and its live feed: TC-2.10, TC-2.15's routing half,
and FR-37's read rules."""

import asyncio
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.domains.notifications.graphql.errors import NotificationNotFoundError
from app.domains.notifications.interactors.dtos import MarkNotificationReadInputDTO
from app.domains.notifications.interactors.mark_all_read import MarkAllReadInteractor
from app.domains.notifications.interactors.mark_notification_read import (
    MarkNotificationReadInteractor,
)
from app.domains.notifications.interfaces.dtos import PublishNotification
from app.domains.notifications.services.live_signal import LiveSignal
from app.domains.notifications.services.notification_service import (
    NotificationService,
)
from tests.fakes.fake_notification_repository import FakeNotificationRepository

NOW = datetime(2026, 9, 24, 13, 30, tzinfo=UTC)


class FakeDeliverySettings:
    def __init__(self, *, popups_enabled: bool) -> None:
        self.enabled = popups_enabled

    async def popups_enabled(self, *, user_id: uuid.UUID) -> bool:
        return self.enabled


def _publish(*, user_id: uuid.UUID, source_id: uuid.UUID) -> PublishNotification:
    return PublishNotification(
        user_id=user_id,
        kind="reminder",
        source_id=source_id,
        target_id=uuid.uuid4(),
        title="Call Mom",
        detail="",
        marker="on_time",
        occurred_at=NOW,
    )


def _service(
    *, repository: FakeNotificationRepository, popups_enabled: bool
) -> NotificationService:
    return NotificationService(
        notification_repository=repository,
        delivery_settings=FakeDeliverySettings(popups_enabled=popups_enabled),
        now_provider=lambda: NOW,
    )


async def test_pop_ups_off_still_lists_the_notification() -> None:
    """TC-2.10, FR-12, FR-13."""
    repository = FakeNotificationRepository()
    user_id = uuid.uuid4()

    notification = await _service(repository=repository, popups_enabled=False).publish(
        publish=_publish(user_id=user_id, source_id=uuid.uuid4())
    )

    assert notification is not None
    assert notification.show_popup is False
    assert await repository.count_unread(user_id=user_id) == 1


async def test_publishing_the_same_firing_twice_writes_one_row() -> None:
    """AD-3."""
    repository = FakeNotificationRepository()
    service = _service(repository=repository, popups_enabled=True)
    publish = _publish(user_id=uuid.uuid4(), source_id=uuid.uuid4())

    first = await service.publish(publish=publish)
    second = await service.publish(publish=publish)

    assert first is not None and first.show_popup is True
    assert second is None
    assert len(repository.rows) == 1


async def test_mark_read_then_mark_all_read() -> None:
    """FR-37: a missing or another user's id reads as not found (NFR-6)."""
    repository = FakeNotificationRepository()
    service = _service(repository=repository, popups_enabled=True)
    user_id = uuid.uuid4()
    first = await service.publish(
        publish=_publish(user_id=user_id, source_id=uuid.uuid4())
    )
    await service.publish(publish=_publish(user_id=user_id, source_id=uuid.uuid4()))
    assert first is not None
    mark_read = MarkNotificationReadInteractor(
        notification_repository=repository, now_provider=lambda: NOW
    )

    read = await mark_read.mark_notification_read(
        dto=MarkNotificationReadInputDTO(user_id=user_id, notification_id=first.id)
    )
    with pytest.raises(NotificationNotFoundError):
        await mark_read.mark_notification_read(
            dto=MarkNotificationReadInputDTO(
                user_id=uuid.uuid4(), notification_id=first.id
            )
        )
    marked = await MarkAllReadInteractor(
        notification_repository=repository,
        now_provider=lambda: NOW + timedelta(minutes=1),
    ).mark_all_read(user_id=user_id)

    assert read.read_at == NOW
    assert marked == 1
    assert await repository.count_unread(user_id=user_id) == 0


async def test_a_signal_reaches_only_the_user_it_names() -> None:
    """TC-2.15, NFR-6: routing happens before any row is read."""
    signal = LiveSignal(channel="test")
    owner, stranger = uuid.uuid4(), uuid.uuid4()
    notification_id = uuid.uuid4()

    async with (
        signal.subscribe(user_id=owner) as owner_feed,
        signal.subscribe(user_id=stranger) as stranger_feed,
    ):
        signal.dispatch_payload(
            payload=json.dumps(
                {"user_id": str(owner), "notification_id": str(notification_id)}
            )
        )
        received = await asyncio.wait_for(owner_feed.next_notification_id(), 1)
        assert stranger_feed.queue.empty()

    assert received == notification_id
    assert signal.subscriptions == {}


def test_a_malformed_signal_is_dropped() -> None:
    signal = LiveSignal(channel="test")
    signal.dispatch_payload(payload="not json")
    signal.dispatch_payload(payload=json.dumps({"user_id": "nope"}))
