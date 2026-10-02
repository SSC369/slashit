"""SQLAlchemy tables for events. Nothing else lives here.

The foreign key to ``auth.users`` is declared in the migration, not here, for
the reason ``records.models`` gives (AD-9 of 000, no mirror of ``auth``).
"""

import uuid
from datetime import date, datetime, time

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Computed,
    Date,
    DateTime,
    Enum,
    Integer,
    Text,
    Time,
    Uuid,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.domains.events.constants import EVENT_EMBEDDING_DIMENSIONS
from app.models import Base

RECORD_ORIGINS = ("command", "edit")


class CalendarEvent(Base):
    """One event. Its schedule is local fields plus a zone; ``starts_at`` and
    ``ends_at`` are the next or only occurrence (build plan AD-2)."""

    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    title: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_date: Mapped[date | None] = mapped_column(Date)
    end_time: Mapped[time | None] = mapped_column(Time)
    repeat_yearly: Mapped[bool] = mapped_column(Boolean)
    schedule_timezone: Mapped[str] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    alert_lead_minutes: Mapped[int | None] = mapped_column(Integer)
    origin: Mapped[str] = mapped_column(
        Enum(*RECORD_ORIGINS, name="record_origin", create_type=False)
    )
    original_input: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # NULL until slice 2's embed job fills it (005 AD-2, AD-7).
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EVENT_EMBEDDING_DIMENSIONS)
    )
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', title || ' ' || coalesce(location, '') "
            "|| ' ' || coalesce(description, ''))",
            persisted=True,
        ),
    )
