"""reminders: one row per reminder, its schedule stored in local terms.

Revision ID: 0016_reminders
Revises: 0015_drop_pw_verify_hook
Create Date: 2026-09-23

Epic 003, sub-plan 4.1. The schedule is kept as a local rule plus the zone it
was computed in (build plan AD-5), with ``next_fire_at`` as the one UTC
instant the firing sweep in slice 2 reads. Soft-deleted, matching tasks since
0013 (FR-29, FR-30).

Rule T2: Row Level Security is enabled, forced, and given a policy in the
same migration that creates the table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016_reminders"
down_revision: str | None = "0015_drop_pw_verify_hook"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

REPEAT_KINDS = ("none", "daily", "weekly", "monthly", "yearly")
REMINDER_STATES = ("upcoming", "fired", "done")
REMINDER_ACTIONS = ("done", "snoozed", "missed")


def upgrade() -> None:
    op.execute(sa.text("CREATE TYPE reminder_repeat_kind AS ENUM " + str(REPEAT_KINDS)))
    op.execute(sa.text("CREATE TYPE reminder_state AS ENUM " + str(REMINDER_STATES)))
    op.execute(sa.text("CREATE TYPE reminder_action AS ENUM " + str(REMINDER_ACTIONS)))

    op.create_table(
        "reminders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "repeat_kind",
            postgresql.ENUM(
                *REPEAT_KINDS, name="reminder_repeat_kind", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("repeat_interval", sa.SmallInteger(), nullable=False),
        sa.Column(
            "repeat_weekdays",
            postgresql.ARRAY(sa.SmallInteger()),
            nullable=False,
            server_default="{}",
        ),
        # Monthly and yearly only: the day asked for, which may exceed the
        # month's length (the 31st, 29 February). The date each month fires is
        # clamped from it (FR-8); anchor_local_date alone cannot hold "31" in a
        # 30-day month. Added during the build; logged in the dev log.
        sa.Column("repeat_month_day", sa.SmallInteger(), nullable=True),
        sa.Column("local_time", sa.Time(), nullable=False),
        sa.Column("anchor_local_date", sa.Date(), nullable=False),
        sa.Column("one_time_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("next_fire_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("schedule_timezone", sa.Text(), nullable=False),
        sa.Column(
            "state",
            postgresql.ENUM(*REMINDER_STATES, name="reminder_state", create_type=False),
            nullable=False,
        ),
        sa.Column("last_fired_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "last_action",
            postgresql.ENUM(
                *REMINDER_ACTIONS, name="reminder_action", create_type=False
            ),
            nullable=True,
        ),
        # record_origin already exists, created by 0003_tasks for tasks.
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
            "repeat_interval BETWEEN 1 AND 99", name="ck_repeat_interval"
        ),
        sa.CheckConstraint(
            "repeat_month_day IS NULL OR repeat_month_day BETWEEN 1 AND 31",
            name="ck_repeat_month_day",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
    )
    # The firing sweep's whole query (slice 2): due rows among live ones.
    op.create_index(
        "ix_reminders_due",
        "reminders",
        ["next_fire_at"],
        postgresql_where=sa.text("deleted_at IS NULL AND state <> 'done'"),
    )
    # Every list and the 100-active cap read by user among live rows.
    op.create_index(
        "ix_reminders_user_deleted_at", "reminders", ["user_id", "deleted_at"]
    )

    _lock_down("reminders")


def downgrade() -> None:
    op.drop_table("reminders")
    op.execute(sa.text("DROP TYPE IF EXISTS reminder_action"))
    op.execute(sa.text("DROP TYPE IF EXISTS reminder_state"))
    op.execute(sa.text("DROP TYPE IF EXISTS reminder_repeat_kind"))


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
