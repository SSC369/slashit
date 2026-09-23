"""SQLAlchemy tables for notifications. Nothing else lives here."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, SmallInteger, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

NOTIFICATION_KINDS = ("reminder", "email_paused")
MARKERS = ("on_time", "late", "missed")
NOTIFICATION_ACTIONS = ("done", "snoozed")
DELIVERY_CHANNELS = ("popup", "email")
DELIVERY_STATUSES = ("queued", "sent", "failed", "skipped")


class Notification(Base):
    """One row in the user's notification list (FR-12, FR-35)."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    kind: Mapped[str] = mapped_column(
        Enum(*NOTIFICATION_KINDS, name="notification_kind", create_type=False)
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    target_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    title: Mapped[str] = mapped_column(Text)
    detail: Mapped[str] = mapped_column(Text)
    marker: Mapped[str] = mapped_column(
        Enum(*MARKERS, name="firing_lateness", create_type=False)
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # The reminder's zone, so the email can say "7:00 PM · Asia/Kolkata".
    time_zone: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    action: Mapped[str | None] = mapped_column(
        Enum(*NOTIFICATION_ACTIONS, name="notification_action", create_type=False)
    )
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class NotificationDelivery(Base):
    """One channel's delivery of one notification (AD-3)."""

    __tablename__ = "notification_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    notification_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    channel: Mapped[str] = mapped_column(
        Enum(*DELIVERY_CHANNELS, name="delivery_channel", create_type=False)
    )
    status: Mapped[str] = mapped_column(
        Enum(*DELIVERY_STATUSES, name="delivery_status", create_type=False)
    )
    attempts: Mapped[int] = mapped_column(SmallInteger)
    provider_message_id: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
