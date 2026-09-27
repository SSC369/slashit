"""Capture history learns forget: a scrubbed turn and a `/forget` turn.

Revision ID: 0028_forget
Revises: 0027_memory_events
Create Date: 2026-09-25

Epic 004, sub-plan 4.2. ``capture_turns`` stays append-only except for one
permitted ``UPDATE`` (build plan AD-3): the scrub that blanks a forgotten
memory's words and stamps ``forgotten_at``. The check constraint below makes a
scrubbed turn that still holds text impossible to write (FR-23).
``affected_count`` is how many memories a confirmed `/forget` removed, so the
turn can read "Forgot 2 memories" without storing what was typed (FR-28).

Not fully reversible: PostgreSQL cannot drop an enum value.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0028_forget"
down_revision: str | None = "0027_memory_events"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TYPE capture_turn_outcome ADD VALUE IF NOT EXISTS 'memory_forgotten'"
        )
    )
    op.add_column(
        "capture_turns",
        sa.Column("forgotten_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "capture_turns",
        sa.Column("affected_count", sa.Integer(), nullable=True),
    )
    op.create_check_constraint(
        "ck_capture_turns_forgotten_holds_no_words",
        "capture_turns",
        "forgotten_at IS NULL OR (input_text = '' AND question_text IS NULL "
        "AND answer_text IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_capture_turns_forgotten_holds_no_words", "capture_turns", type_="check"
    )
    op.drop_column("capture_turns", "affected_count")
    op.drop_column("capture_turns", "forgotten_at")
