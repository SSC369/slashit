"""calendar_events: one row per event, its schedule stored in local terms.

Revision ID: 0037_calendar_events
Revises: 0036_event_properties
Create Date: 2026-10-02

Epic 007, sub-plan 4.1. Named ``calendar_events`` because analytics already
owns ``events`` (build plan Q1). The schedule is local fields plus the zone
it was set in; ``starts_at`` and ``ends_at`` are the next or only occurrence
as UTC instants, derived by ``events.services.schedule`` (build plan AD-2).
Soft-deleted, as every record type is.

Rule T2: Row Level Security is enabled, forced, granted and policed in the
same migration that creates the table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0037_calendar_events"
down_revision: str | None = "0036_event_properties"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

EMBEDDING_DIMENSIONS = 768


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column(
            "repeat_yearly", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("schedule_timezone", sa.Text(), nullable=False),
        sa.Column("starts_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("ends_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("alert_lead_minutes", sa.Integer(), nullable=True),
        # record_origin already exists, created by 0003_tasks.
        sa.Column(
            "origin",
            postgresql.ENUM("command", "edit", name="record_origin", create_type=False),
            nullable=False,
        ),
        sa.Column("original_input", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "char_length(title) BETWEEN 1 AND 200", name="ck_event_title_length"
        ),
        sa.CheckConstraint(
            "location IS NULL OR char_length(location) <= 200",
            name="ck_event_location_length",
        ),
        sa.CheckConstraint(
            "description IS NULL OR char_length(description) <= 2000",
            name="ck_event_description_length",
        ),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="ck_event_end_date"
        ),
        sa.CheckConstraint(
            "start_time IS NOT NULL OR end_time IS NULL", name="ck_event_end_time"
        ),
        sa.CheckConstraint(
            "alert_lead_minutes IS NULL OR alert_lead_minutes BETWEEN 0 AND 525600",
            name="ck_event_alert_lead",
        ),
        sa.CheckConstraint("ends_at >= starts_at", name="ck_event_instants"),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
    )
    # Search columns on the record's own table (005 AD-2), added by SQL because
    # SQLAlchemy core has no vector or generated tsvector type, as in 0033.
    # The vector is filled by slice 2's embed job.
    op.execute(
        sa.text(
            "ALTER TABLE calendar_events ADD COLUMN embedding "
            f"vector({EMBEDDING_DIMENSIONS})"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE calendar_events ADD COLUMN search_vector tsvector "
            "GENERATED ALWAYS AS (to_tsvector('english', title || ' ' || "
            "coalesce(location, '') || ' ' || coalesce(description, ''))) STORED"
        )
    )
    # Every list, the 500-upcoming cap and 010's Today view read by user and time.
    op.create_index(
        "ix_calendar_events_user_starts_at",
        "calendar_events",
        ["user_id", "starts_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_calendar_events_search_vector",
        "calendar_events",
        ["search_vector"],
        postgresql_using="gin",
    )

    _lock_down("calendar_events")


def downgrade() -> None:
    op.drop_table("calendar_events")


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
