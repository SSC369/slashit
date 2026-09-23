"""user_settings: the four reminder settings.

Revision ID: 0017_reminder_settings
Revises: 0016_reminders
Create Date: 2026-09-23

Epic 003, sub-plan 4.1, build plan AD-10. The defaults are the PRD's: a
default reminder time of 09:00 (FR-31) and both channel switches on (FR-32).
Slice 1 only reads ``default_reminder_time``; the Settings controls for all
four land in slice 3. Existing rows take the defaults, so no backfill.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_reminder_settings"
down_revision: str | None = "0016_reminders"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column(
            "default_reminder_time",
            sa.Time(),
            nullable=False,
            server_default=sa.text("'09:00'"),
        ),
    )
    op.add_column(
        "user_settings",
        sa.Column(
            "popups_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.add_column(
        "user_settings",
        sa.Column(
            "email_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.add_column(
        "user_settings",
        sa.Column("channels_off_warned_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "channels_off_warned_at")
    op.drop_column("user_settings", "email_enabled")
    op.drop_column("user_settings", "popups_enabled")
    op.drop_column("user_settings", "default_reminder_time")
