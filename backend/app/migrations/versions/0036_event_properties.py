"""events: a numbers-only `properties` column, for search's counts and positions.

Revision ID: 0036_event_properties
Revises: 0035_search_events
Create Date: 2026-09-30

Epic 005, sub-plan 4.2, added to the index by change record on 2026-09-30
(dev log Q1). The PRD's section 8 metrics need a result's position and a
search's counts; the table held only a type and a time.

The check constraint is the T6 guarantee in the database, not only in code:
every value is a number or a boolean, so no text, and therefore no search or
record text, can ever be stored here. Nested objects and arrays are refused
too, since they could hold strings.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0036_event_properties"
down_revision: str | None = "0035_search_events"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("properties", postgresql.JSONB(), nullable=True),
    )
    op.create_check_constraint(
        "ck_events_properties_numbers_only",
        "events",
        "properties IS NULL OR ("
        "jsonb_typeof(properties) = 'object' AND NOT jsonb_path_exists("
        # Strict mode: lax mode unwraps an array value into its members, so
        # {"list": [1, 2]} would pass as two numbers.
        'properties, \'strict $.* ? (@.type() != "number" && @.type() != "boolean")\''
        "))",
    )


def downgrade() -> None:
    op.drop_constraint("ck_events_properties_numbers_only", "events", type_="check")
    op.drop_column("events", "properties")
