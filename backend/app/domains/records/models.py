"""SQLAlchemy tables for records. Nothing else lives here.

The foreign key to ``auth.users`` is declared in the migration, not here, for
the same reason gateway's models do it that way: identity lives in Supabase's
``auth`` schema, which decision AD-9 says we do not mirror, so SQLAlchemy has
no table in its metadata to point a ``ForeignKey`` at.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

TASK_STATUSES = ("pending", "done")
TASK_ORIGINS = ("command", "edit")


class Task(Base):
    """One task. The first and only record type this epic ships."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    title: Mapped[str] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        Enum(*TASK_STATUSES, name="task_status", create_type=False)
    )
    origin: Mapped[str] = mapped_column(
        Enum(*TASK_ORIGINS, name="record_origin", create_type=False)
    )
    original_input: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
