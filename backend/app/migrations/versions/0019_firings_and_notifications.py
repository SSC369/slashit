"""Firings and notifications: what fired, what the user was told, and how.

Revision ID: 0019_firings_and_notifications
Revises: 0018_pending_capture_remind
Create Date: 2026-09-23

Epic 003, sub-plan 4.2. Three tables carry the exactly-once rule (build plan
AD-3) through their unique constraints, never through job scheduling:

- ``reminder_firings``: one row per occurrence, ``UNIQUE (reminder_id,
  scheduled_for)``.
- ``notifications``: one list row per firing, ``UNIQUE (source_id)`` for kind
  ``reminder``.
- ``notification_deliveries``: one row per channel, ``UNIQUE (notification_id,
  channel)``.

``reminders`` gains ``snoozed_until``: a snooze is a one-off extra firing that
leaves the series alone (sub-plan 4.2, decision 1).

``notifications`` also carries ``target_id``, ``occurred_at``, ``action`` and
``acted_at``, which the build plan's data model did not list. The panel needs
them to open the reminder and to read "due Sun 6:00 PM, delivered Mon 4:10 PM"
and "marked done 9:41 AM". Logged in the dev log.

Rule T2: every new table enables and forces Row Level Security with an owner
policy in this migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_firings_and_notifications"
down_revision: str | None = "0018_pending_capture_remind"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

LATENESS = ("on_time", "late", "missed")
NOTIFICATION_KINDS = ("reminder", "email_paused")
DELIVERY_CHANNELS = ("popup", "email")
DELIVERY_STATUSES = ("queued", "sent", "failed", "skipped")
NOTIFICATION_ACTIONS = ("done", "snoozed")


def upgrade() -> None:
    op.execute(sa.text("CREATE TYPE firing_lateness AS ENUM " + str(LATENESS)))
    op.execute(
        sa.text("CREATE TYPE notification_kind AS ENUM " + str(NOTIFICATION_KINDS))
    )
    op.execute(
        sa.text("CREATE TYPE delivery_channel AS ENUM " + str(DELIVERY_CHANNELS))
    )
    op.execute(sa.text("CREATE TYPE delivery_status AS ENUM " + str(DELIVERY_STATUSES)))
    op.execute(
        sa.text("CREATE TYPE notification_action AS ENUM " + str(NOTIFICATION_ACTIONS))
    )

    op.add_column(
        "reminders",
        sa.Column("snoozed_until", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    # The sweep reads LEAST(next_fire_at, snoozed_until); this index serves
    # the snooze half, as ix_reminders_due serves the other.
    op.create_index(
        "ix_reminders_snoozed",
        "reminders",
        ["snoozed_until"],
        postgresql_where=sa.text("snoozed_until IS NOT NULL AND deleted_at IS NULL"),
    )

    _create_firings()
    _create_notifications()
    _create_deliveries()

    for table in ("reminder_firings", "notifications", "notification_deliveries"):
        _lock_down(table)


def downgrade() -> None:
    op.drop_table("notification_deliveries")
    op.drop_table("notifications")
    op.drop_table("reminder_firings")
    op.drop_index("ix_reminders_snoozed", table_name="reminders")
    op.drop_column("reminders", "snoozed_until")
    for enum_name in (
        "notification_action",
        "delivery_status",
        "delivery_channel",
        "notification_kind",
        "firing_lateness",
    ):
        op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))


def _create_firings() -> None:
    op.create_table(
        "reminder_firings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("reminder_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("scheduled_for", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("fired_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "lateness",
            postgresql.ENUM(*LATENESS, name="firing_lateness", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "action",
            postgresql.ENUM(
                "done", "snoozed", "missed", name="reminder_action", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("acted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "reminder_id", "scheduled_for", name="uq_reminder_firings_occurrence"
        ),
        sa.ForeignKeyConstraint(["reminder_id"], ["reminders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
    )


def _create_notifications() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            postgresql.ENUM(
                *NOTIFICATION_KINDS, name="notification_kind", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "marker",
            postgresql.ENUM(*LATENESS, name="firing_lateness", create_type=False),
            nullable=False,
        ),
        sa.Column("occurred_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("read_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "action",
            postgresql.ENUM(
                *NOTIFICATION_ACTIONS, name="notification_action", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("acted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
    )
    # AD-3: one list row per firing.
    op.create_index(
        "uq_notifications_reminder_source",
        "notifications",
        ["source_id"],
        unique=True,
        postgresql_where=sa.text("kind = 'reminder'"),
    )
    # The panel's page, newest first (FR-35).
    op.create_index(
        "ix_notifications_user_created",
        "notifications",
        ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    # The bell's count (FR-36).
    op.create_index(
        "ix_notifications_unread",
        "notifications",
        ["user_id"],
        postgresql_where=sa.text("read_at IS NULL"),
    )


def _create_deliveries() -> None:
    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("notification_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "channel",
            postgresql.ENUM(
                *DELIVERY_CHANNELS, name="delivery_channel", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                *DELIVERY_STATUSES, name="delivery_status", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("attempts", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("provider_message_id", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "notification_id", "channel", name="uq_notification_deliveries_channel"
        ),
        sa.ForeignKeyConstraint(
            ["notification_id"], ["notifications.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
    )


def _lock_down(table: str) -> None:
    """Enable, force, grant and police. See 0001_ai_usage for why all four."""
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
