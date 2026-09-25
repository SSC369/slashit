"""SQLAlchemy tables for reminders. Nothing else lives here.

The foreign key to ``auth.users`` is declared in the migration, not here, for
the reason ``records.models`` gives (AD-9, no mirror of Supabase's ``auth``).
"""

import uuid
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, SmallInteger, Text, Time, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

REPEAT_KINDS = ("none", "daily", "weekly", "monthly", "yearly")
REMINDER_STATES = ("upcoming", "fired", "done")
REMINDER_ACTIONS = ("done", "snoozed", "missed")
RECORD_ORIGINS = ("command", "edit")


class Reminder(Base):
    """One reminder. Its schedule is a local rule; ``next_fire_at`` is the one
    UTC instant the firing sweep reads (build plan AD-5)."""

    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    description: Mapped[str] = mapped_column(Text)
    repeat_kind: Mapped[str] = mapped_column(
        Enum(*REPEAT_KINDS, name="reminder_repeat_kind", create_type=False)
    )
    repeat_interval: Mapped[int] = mapped_column(SmallInteger)
    repeat_weekdays: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger))
    repeat_month_day: Mapped[int | None] = mapped_column(SmallInteger)
    local_time: Mapped[time] = mapped_column(Time)
    anchor_local_date: Mapped[date] = mapped_column(Date)
    one_time_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_fire_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    schedule_timezone: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(
        Enum(*REMINDER_STATES, name="reminder_state", create_type=False)
    )
    last_fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_action: Mapped[str | None] = mapped_column(
        Enum(*REMINDER_ACTIONS, name="reminder_action", create_type=False)
    )
    origin: Mapped[str] = mapped_column(
        Enum(*RECORD_ORIGINS, name="record_origin", create_type=False)
    )
    original_input: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # A snooze is a one-off extra firing; the series stays in next_fire_at.
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


FIRING_LATENESS = ("on_time", "late", "missed")


class ReminderFiring(Base):
    """One occurrence that fired. ``UNIQUE (reminder_id, scheduled_for)`` is
    what makes a repeated firing job a no-op (AD-3)."""

    __tablename__ = "reminder_firings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    reminder_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lateness: Mapped[str] = mapped_column(
        Enum(*FIRING_LATENESS, name="firing_lateness", create_type=False)
    )
    action: Mapped[str | None] = mapped_column(
        Enum(*REMINDER_ACTIONS, name="reminder_action", create_type=False)
    )
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
