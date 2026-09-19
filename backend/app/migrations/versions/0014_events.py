"""events: an insert-only instrumentation log, for PRD section 8's metrics
that have no data source today.

Revision ID: 0014_events
Revises: 0013_tasks_soft_delete
Create Date: 2026-09-19

Two event types, both closing a real gap the 2026-09-14 metrics audit
recorded in 001's dev log: a session where the user typed without a command
(FR-9), and a records view being opened. Prompt content never reaches this
table, per repo-rules.md section 16's rule on analytics tables.

Rule T2: Row Level Security is enabled, forced, and given a policy in the
same migration that creates the table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_events"
down_revision: str | None = "0013_tasks_soft_delete"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

EVENT_TYPES = ("no_command_input", "records_view_opened")


def upgrade() -> None:
    op.execute(sa.text("CREATE TYPE event_type AS ENUM " + str(EVENT_TYPES)))

    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_type",
            postgresql.ENUM(*EVENT_TYPES, name="event_type", create_type=False),
            nullable=False,
        ),
        sa.Column("occurred_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_events_user_type_occurred",
        "events",
        ["user_id", "event_type", "occurred_at"],
    )

    _lock_down("events")


def downgrade() -> None:
    op.drop_index("ix_events_user_type_occurred", table_name="events")
    op.drop_table("events")
    op.execute(sa.text("DROP TYPE IF EXISTS event_type"))


def _lock_down(table: str) -> None:
    """Enable, force, grant and police. All four, or isolation does not bind.

    See 0001_ai_usage for why each of the four statements is required.
    """
    op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
    op.execute(
        sa.text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO authenticated")
    )
    op.execute(
        sa.text(
            f"CREATE POLICY {table}_own_rows ON {table} FOR ALL "
            "USING (user_id = NULLIF("
            "current_setting('request.jwt.claims', true)::jsonb ->> 'sub', ''"
            ")::uuid)"
        )
    )
