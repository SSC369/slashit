"""SQLAlchemy tables for expenses. Nothing else lives here.

The foreign key to ``auth.users`` is declared in the migration, not here, for
the reason ``records.models`` gives (AD-9, no mirror of Supabase's ``auth``).
"""

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Computed, Date, DateTime, Enum, Text, Uuid
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.domains.expenses.constants import (
    EXPENSE_CATEGORIES,
    EXPENSE_EMBEDDING_DIMENSIONS,
)
from app.models import Base

RECORD_ORIGINS = ("command", "edit")


class Expense(Base):
    """One spend. Money is integer paise (build plan AD-2) and the day is a
    local calendar date, never a timestamp (AD-3)."""

    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    amount_paise: Mapped[int] = mapped_column(BigInteger)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(
        Enum(*EXPENSE_CATEGORIES, name="expense_category", create_type=False)
    )
    spent_on: Mapped[date] = mapped_column(Date)
    origin: Mapped[str] = mapped_column(
        Enum(*RECORD_ORIGINS, name="record_origin", create_type=False)
    )
    original_input: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # NULL until slice 3's embed job fills it, and NULL again after a
    # description edit, so an old meaning never matches.
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EXPENSE_EMBEDDING_DIMENSIONS)
    )
    # Generated from description and category; 0037_expenses holds the full
    # expression. Declared Computed only so the ORM never writes it.
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', description)", persisted=True)
    )
