"""tasks: search columns for epic 005's search.

Revision ID: 0032_task_search
Revises: 0031_drop_forget_turns
Create Date: 2026-09-30

Epic 005, sub-plan 4.1, build plan AD-2. ``search_vector`` is generated from
``title`` for word matching (FR-4). ``embedding`` holds the task's meaning
(FR-5); it is NULL until the ``records.embed_task`` job fills it after commit, and
NULL again after the title is edited, so an old meaning never matches (FR-14).

Row Level Security is already forced on this table, with its policy, by the
migration that created it (T2); new columns inherit it.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0032_task_search"
down_revision: str | None = "0031_drop_forget_turns"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

EMBEDDING_DIMENSIONS = 768


def upgrade() -> None:
    # Added by SQL because SQLAlchemy core has no vector or generated tsvector
    # column type without the ORM model, as in 0024_memories.
    op.execute(
        sa.text(
            f"ALTER TABLE tasks ADD COLUMN embedding vector({EMBEDDING_DIMENSIONS})"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE tasks ADD COLUMN search_vector tsvector "
            "GENERATED ALWAYS AS (to_tsvector('english', title)) STORED"
        )
    )
    op.create_index(
        "ix_tasks_search_vector",
        "tasks",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_search_vector", table_name="tasks")
    op.drop_column("tasks", "search_vector")
    op.drop_column("tasks", "embedding")
