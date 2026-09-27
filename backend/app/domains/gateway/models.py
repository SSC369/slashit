"""SQLAlchemy tables for the gateway. Nothing else lives here.

**The foreign key to ``auth.users`` is declared in the migration, not here.**
Identity lives in Supabase's ``auth`` schema, which decision AD-9 says we do not
mirror, so SQLAlchemy has no table in its metadata to point a ``ForeignKey`` at
and raises ``NoReferencedTableError`` if you try. The database still enforces the
constraint; the ORM simply does not know about it, which is correct because
nothing ever navigates from a usage row to a user object.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Index,
    Integer,
    Numeric,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

OUTCOMES = (
    "success",
    "user_limit_reached",
    "shared_quota_exhausted",
    "provider_unavailable",
    "provider_timeout",
    "malformed_result",
)

# Epic 004, migration 0026. Tech stack T9: the per-user cap counts
# generations only.
OPERATIONS = ("generate", "embed")


class AiUsage(Base):
    """One row per model call, counts only.

    Requirement FR-12: no column here can hold prompt or response text. Adding
    one would be a defect, and ``test_usage_row_holds_no_user_text`` fails if
    anyone does.
    """

    __tablename__ = "ai_usage"
    __table_args__ = (Index("ix_ai_usage_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    provider: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 8), default=0)
    outcome: Mapped[str] = mapped_column(
        Enum(*OUTCOMES, name="ai_call_outcome", create_type=False)
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operation: Mapped[str] = mapped_column(
        Enum(*OPERATIONS, name="ai_operation", create_type=False),
        default="generate",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AiUserLimit(Base):
    """The per-user ceiling. A row, not a constant, so FR-10 holds."""

    __tablename__ = "ai_user_limit"
    __table_args__ = (
        CheckConstraint(
            "requests_per_day >= 0", name="ck_requests_per_day_non_negative"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    plan: Mapped[str] = mapped_column(Text, default="free")
    requests_per_day: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
