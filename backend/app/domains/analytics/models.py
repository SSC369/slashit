"""SQLAlchemy tables for analytics. Nothing else lives here."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

EVENT_TYPES = (
    "no_command_input",
    "records_view_opened",
    # Epic 004, migration 0027.
    "memory_saved",
    "memory_lookup",
    "memory_conflict_answered",
    "memory_forgotten",
    "memory_category_edited",
    "memory_secret_caution",
)


class Event(Base):
    """One instrumentation event. Insert-only, never updated or deleted.

    Closes the two buildable gaps from 001's PRD section 8 metrics audit,
    2026-09-14: a session where the user typed without a command (FR-9), and
    a records view being opened. Never carries prompt content, per
    repo-rules.md section 16.
    """

    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    event_type: Mapped[str] = mapped_column(
        Enum(*EVENT_TYPES, name="event_type", create_type=False)
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
