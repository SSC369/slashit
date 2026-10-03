"""events: seven expense event types, for the PRD's section 8 metrics.

Revision ID: 0041_expense_events
Revises: 0040_capture_expense
Create Date: 2026-10-02

Epic 006, sub-plan 4.1. All seven are added now so slices 2 and 3 need no
migration. Each event carries ids, counts and booleans only, never a
description or an amount (tech stack T6, build plan AD-9).

Not reversible: PostgreSQL cannot drop an enum value.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0041_expense_events"
down_revision: str | None = "0040_capture_expense"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

EXPENSE_EVENT_TYPES = (
    "expense_saved",
    "expense_summary_viewed",
    "expense_amount_asked",
    "expense_currency_refused",
    "expense_amount_edited",
    "expense_category_edited",
    "expense_deleted",
)


def upgrade() -> None:
    for event_type in EXPENSE_EVENT_TYPES:
        op.execute(
            sa.text(f"ALTER TYPE event_type ADD VALUE IF NOT EXISTS '{event_type}'")
        )


def downgrade() -> None:
    """Nothing to undo that PostgreSQL allows; the values stay, unused."""
