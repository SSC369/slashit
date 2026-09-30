"""Capture learns search: a `search_text` question and a `searched` outcome.

Revision ID: 0034_search_capture
Revises: 0033_reminder_search
Create Date: 2026-09-30

Epic 005, sub-plan 4.1. ``pending_captures`` gains the missing field
``search_text`` for FR-2's one question. ``capture_turns`` gains the outcome
``searched``; the turn keeps only the typed line, never results or an answer
(FR-21).

Not reversible: PostgreSQL cannot drop an enum value.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0034_search_capture"
down_revision: str | None = "0033_reminder_search"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TYPE pending_capture_missing_field "
            "ADD VALUE IF NOT EXISTS 'search_text'"
        )
    )
    op.execute(
        sa.text("ALTER TYPE capture_turn_outcome ADD VALUE IF NOT EXISTS 'searched'")
    )


def downgrade() -> None:
    """Nothing to undo that PostgreSQL allows; the values stay, unused."""
