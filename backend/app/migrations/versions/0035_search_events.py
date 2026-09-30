"""events: four search event types, for the PRD's section 8 metrics.

Revision ID: 0035_search_events
Revises: 0034_search_capture
Create Date: 2026-09-30

Epic 005, sub-plan 4.1. All four are added now so slices 2 and 3 need no
migration. Each event carries counts, types and positions only, never search
or record text (tech stack T6, build plan AD-10).

Not reversible: PostgreSQL cannot drop an enum value.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0035_search_events"
down_revision: str | None = "0034_search_capture"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

SEARCH_EVENT_TYPES = (
    "search_run",
    "search_result_opened",
    "answer_citation_opened",
    "related_opened",
)


def upgrade() -> None:
    for event_type in SEARCH_EVENT_TYPES:
        op.execute(
            sa.text(f"ALTER TYPE event_type ADD VALUE IF NOT EXISTS '{event_type}'")
        )


def downgrade() -> None:
    """Nothing to undo that PostgreSQL allows; the values stay, unused."""
