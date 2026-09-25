"""SQLAlchemy tables for capture. Nothing else lives here."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

MISSING_FIELDS = ("title", "due_at", "remind_at")
CAPTURE_TURN_OUTCOMES = (
    "task_created",
    "question_asked",
    "discarded",
    "refused",
    "reminder_created",
)


class PendingCapture(Base):
    """One unanswered question. FR-37: answerable at any later point, so this
    is a table, not a session or a cache entry, per build plan AD-2."""

    __tablename__ = "pending_captures"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    command_name: Mapped[str] = mapped_column(Text)
    known_title: Mapped[str | None] = mapped_column(Text)
    missing_field: Mapped[str] = mapped_column(
        Enum(*MISSING_FIELDS, name="pending_capture_missing_field", create_type=False)
    )
    question_text: Mapped[str] = mapped_column(Text)
    original_input: Mapped[str] = mapped_column(Text)
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CaptureTurn(Base):
    """A log of one capture attempt, retained after its outcome. FR-44: never
    updated or deleted, unlike PendingCapture which this outlives."""

    __tablename__ = "capture_turns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    input_text: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(
        Enum(*CAPTURE_TURN_OUTCOMES, name="capture_turn_outcome", create_type=False)
    )
    resulting_task_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    resulting_pending_capture_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    # Epic 003, migration 0018. No foreign key, as for resulting_task_id.
    resulting_reminder_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    question_text: Mapped[str | None] = mapped_column(Text)
    answer_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
