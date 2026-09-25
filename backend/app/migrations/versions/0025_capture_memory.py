"""Capture learns memories: a `fact` question and two memory turn outcomes.

Revision ID: 0025_capture_memory
Revises: 0024_memories
Create Date: 2026-09-25

Epic 004, sub-plan 4.1. ``pending_captures`` gains the missing field ``fact``
for FR-3's one question. ``capture_turns`` gains ``memory_saved`` and
``memory_listed`` and a ``resulting_memory_id`` column, which slice 3's forget
reads to find the turns whose words it must erase.

Not fully reversible: PostgreSQL cannot drop an enum value. Downgrade drops
the column and leaves the enum values in place, unused.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025_capture_memory"
down_revision: str | None = "0024_memories"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TYPE pending_capture_missing_field ADD VALUE IF NOT EXISTS 'fact'"
        )
    )
    for outcome in ("memory_saved", "memory_listed"):
        op.execute(
            sa.text(
                f"ALTER TYPE capture_turn_outcome ADD VALUE IF NOT EXISTS '{outcome}'"
            )
        )
    # No foreign key, for the reason 0006 gives resulting_task_id.
    op.add_column(
        "capture_turns",
        sa.Column("resulting_memory_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        "ix_capture_turns_resulting_memory",
        "capture_turns",
        ["resulting_memory_id"],
        postgresql_where=sa.text("resulting_memory_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_capture_turns_resulting_memory", table_name="capture_turns")
    op.drop_column("capture_turns", "resulting_memory_id")
