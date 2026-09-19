"""tasks: soft delete, no user record is ever hard-deleted.

Revision ID: 0013_tasks_soft_delete
Revises: 0012_backfill_avatar_url
Create Date: 2026-09-19

User decision 2026-09-19: ``deleteTask`` stops running a hard ``DELETE`` and
sets ``deleted_at`` instead. Every read path filters ``deleted_at IS NULL``.
Also closes part of the PRD section 8 metrics gap: a delete is now visible to
audit the same way an edit already was, through a timestamp on the row.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_tasks_soft_delete"
down_revision: str | None = "0012_backfill_avatar_url"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tasks", sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True)
    )
    # Every list and detail read filters this column; without the index it is
    # a sequential scan on every query, same reasoning as ix_tasks_user_due.
    op.create_index("ix_tasks_user_deleted_at", "tasks", ["user_id", "deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_tasks_user_deleted_at", table_name="tasks")
    op.drop_column("tasks", "deleted_at")
