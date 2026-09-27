"""A save that contradicts a memory waits as a pending conflict.

Revision ID: 0029_memory_conflicts
Revises: 0028_forget
Create Date: 2026-09-27

Epic 004, sub-plan 4.3 (build plan AD-6). The conflict lives in
``pending_captures`` beside 001's questions, so "1 question waiting" and the
answer-later rules stay one mechanism. The row holds the new fact and the ids
of the memories it contradicts, never their text: old memories are read live
by id (index section 4). ``candidate_category`` reuses ``memory_category`` so
a resolved save stores exactly what the judgement decided.

Not fully reversible: PostgreSQL cannot drop an enum value.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0029_memory_conflicts"
down_revision: str | None = "0028_forget"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TYPE pending_capture_missing_field "
            "ADD VALUE IF NOT EXISTS 'memory_conflict'"
        )
    )
    op.execute(
        sa.text(
            "ALTER TYPE capture_turn_outcome "
            "ADD VALUE IF NOT EXISTS 'memory_conflict_resolved'"
        )
    )
    op.add_column(
        "pending_captures", sa.Column("candidate_text", sa.Text(), nullable=True)
    )
    op.add_column(
        "pending_captures",
        sa.Column(
            "candidate_category",
            postgresql.ENUM(name="memory_category", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "pending_captures",
        sa.Column(
            "conflicting_memory_ids",
            postgresql.ARRAY(sa.Uuid()),
            nullable=True,
        ),
    )
    # A new enum value cannot be named in the same transaction that added it,
    # so the check compares the conflict columns to each other instead: a row
    # that carries a candidate carries its ids, and the reverse.
    op.create_check_constraint(
        "ck_pending_captures_conflict_complete",
        "pending_captures",
        "(candidate_text IS NULL AND conflicting_memory_ids IS NULL) OR "
        "(candidate_text IS NOT NULL AND conflicting_memory_ids IS NOT NULL "
        "AND cardinality(conflicting_memory_ids) > 0)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_pending_captures_conflict_complete", "pending_captures", type_="check"
    )
    op.drop_column("pending_captures", "conflicting_memory_ids")
    op.drop_column("pending_captures", "candidate_category")
    op.drop_column("pending_captures", "candidate_text")
