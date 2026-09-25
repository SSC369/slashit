"""notifications.time_zone: the reminder's zone, for the email's set time.

Revision ID: 0021_notification_time_zone
Revises: 0020_procrastinate_schema
Create Date: 2026-09-23

Epic 003, sub-plan 4.3, decision 3. The email says "Today, 7:00 PM ·
Asia/Kolkata" (FR-15). The email job reads only notifications and identity;
it may not ask reminders, which already depends on notifications. So the zone
is kept on the notification beside ``occurred_at``. Rows from before this
migration read as UTC.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021_notification_time_zone"
down_revision: str | None = "0020_procrastinate_schema"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column("time_zone", sa.Text(), nullable=False, server_default="UTC"),
    )


def downgrade() -> None:
    op.drop_column("notifications", "time_zone")
