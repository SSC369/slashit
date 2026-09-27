"""SQLAlchemy tables for memories. Nothing else lives here.

The foreign key to ``auth.users`` is declared in the migration, not here, for
the reason ``records/models.py`` gives.
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, DateTime, Enum, Text, Uuid
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.domains.memories.constants import MEMORY_EMBEDDING_DIMENSIONS
from app.models import Base

MEMORY_CATEGORIES = ("personal", "people", "professional", "life")
MEMORY_ORIGINS = ("command", "edit")


class Memory(Base):
    """One fact. A forgotten row keeps only its id, owner and timestamps: the
    check constraint in migration 0024 refuses any other shape (AD-2)."""

    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    text: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(
        Enum(*MEMORY_CATEGORIES, name="memory_category", create_type=False)
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(MEMORY_EMBEDDING_DIMENSIONS)
    )
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(text, ''))", persisted=True),
    )
    origin: Mapped[str] = mapped_column(
        Enum(*MEMORY_ORIGINS, name="record_origin", create_type=False)
    )
    original_input: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
