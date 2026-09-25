"""notifications.deleted_at: the 90-day purge soft-deletes (FR-40).

Revision ID: 0022_notifications_soft_delete
Revises: 0021_notification_time_zone
Create Date: 2026-09-23

Epic 003, sub-plan 4.4, decision 1. A notification older than 90 days leaves
the list by a ``deleted_at`` stamp; the row stays, per the user's standing rule
against hard deletes. The unread index is rebuilt so the bell's count skips
deleted rows without reading them.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0022_notifications_soft_delete"
down_revision: str | None = "0021_notification_time_zone"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.drop_index("ix_notifications_unread", table_name="notifications")
    op.create_index(
        "ix_notifications_unread",
        "notifications",
        ["user_id"],
        postgresql_where=sa.text("read_at IS NULL AND deleted_at IS NULL"),
    )
    # The daily purge finds live rows past the cutoff.
    op.create_index(
        "ix_notifications_live_created",
        "notifications",
        ["created_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_live_created", table_name="notifications")
    op.drop_index("ix_notifications_unread", table_name="notifications")
    op.create_index(
        "ix_notifications_unread",
        "notifications",
        ["user_id"],
        postgresql_where=sa.text("read_at IS NULL"),
    )
    op.drop_column("notifications", "deleted_at")
