"""Capture learns reminders: a `remind_at` question and a `reminder_created` turn.

Revision ID: 0018_pending_capture_remind
Revises: 0017_reminder_settings
Create Date: 2026-09-23

Epic 003, sub-plan 4.1. ``pending_captures`` gains the missing field
``remind_at`` for FR-2's one question; ``known_title`` carries the reminder
text. ``capture_turns`` gains the outcome ``reminder_created`` and a
``resulting_reminder_id`` column, so a ``/remind`` turn appears in capture
history like a ``/add-task`` one. The capture_turns half was not named in the
sub-plan and is logged as a deviation in the feature's dev log.

Not fully reversible: PostgreSQL cannot drop an enum value. Downgrade drops
the column and leaves both enum values in place, unused.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_pending_capture_remind"
down_revision: str | None = "0017_reminder_settings"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "ALTER TYPE pending_capture_missing_field "
            "ADD VALUE IF NOT EXISTS 'remind_at'"
        )
    )
    op.execute(
        sa.text(
            "ALTER TYPE capture_turn_outcome ADD VALUE IF NOT EXISTS 'reminder_created'"
        )
    )
    # No foreign key, for the reason 0006 gives resulting_task_id: this log
    # outlives the row it points at.
    op.add_column(
        "capture_turns",
        sa.Column("resulting_reminder_id", sa.Uuid(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("capture_turns", "resulting_reminder_id")
