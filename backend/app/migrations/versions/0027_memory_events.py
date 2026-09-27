"""events: six memory event types, for the PRD's section 8 metrics.

Revision ID: 0027_memory_events
Revises: 0026_usage_operation
Create Date: 2026-09-25

Epic 004, sub-plan 4.1. All six are added now so slices 2 and 3 need no
migration for their events. Each event carries ids and counts only, never
memory text (tech stack T6, build plan AD-9).

Not reversible: PostgreSQL cannot drop an enum value.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027_memory_events"
down_revision: str | None = "0026_usage_operation"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

MEMORY_EVENT_TYPES = (
    "memory_saved",
    "memory_lookup",
    "memory_conflict_answered",
    "memory_forgotten",
    "memory_category_edited",
    "memory_secret_caution",
)


def upgrade() -> None:
    for event_type in MEMORY_EVENT_TYPES:
        op.execute(
            sa.text(f"ALTER TYPE event_type ADD VALUE IF NOT EXISTS '{event_type}'")
        )


def downgrade() -> None:
    """Nothing to undo that PostgreSQL allows; the values stay, unused."""
