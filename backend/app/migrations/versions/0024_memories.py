"""memories: one fact per row, its category and its meaning vector.

Revision ID: 0024_memories
Revises: 0023_pgvector
Create Date: 2026-09-25

Epic 004, sub-plan 4.1. A forgotten memory is a tombstone (build plan AD-2):
the row stays with ``deleted_at`` set and every readable column set to NULL.
The check constraint below makes that a database guarantee, so a forget that
left the text behind fails at write time rather than passing review.

``search_vector`` is generated from ``text`` for FR-20's keyword lookup, and is
NULL on a tombstone along with the text it came from.

Rule T2: Row Level Security is enabled, forced, and given a policy in the
same migration that creates the table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0024_memories"
down_revision: str | None = "0023_pgvector"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

MEMORY_CATEGORIES = ("personal", "people", "professional", "life")
EMBEDDING_DIMENSIONS = 768


def upgrade() -> None:
    op.execute(sa.text("CREATE TYPE memory_category AS ENUM " + str(MEMORY_CATEGORIES)))

    op.create_table(
        "memories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column(
            "category",
            postgresql.ENUM(
                *MEMORY_CATEGORIES, name="memory_category", create_type=False
            ),
            nullable=True,
        ),
        # record_origin already exists, created by 0003_tasks.
        sa.Column(
            "origin",
            postgresql.ENUM(name="record_origin", create_type=False),
            nullable=False,
        ),
        sa.Column("original_input", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "deleted_at IS NOT NULL OR text IS NOT NULL",
            name="ck_memories_live_has_text",
        ),
    )
    # Added by SQL because SQLAlchemy core has no vector or generated tsvector
    # column type without the ORM model.
    op.execute(
        sa.text(
            f"ALTER TABLE memories ADD COLUMN embedding vector({EMBEDDING_DIMENSIONS})"
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE memories ADD COLUMN search_vector tsvector "
            "GENERATED ALWAYS AS (to_tsvector('english', coalesce(text, ''))) STORED"
        )
    )
    op.create_check_constraint(
        "ck_memories_forgotten_holds_nothing",
        "memories",
        "deleted_at IS NULL OR (text IS NULL AND original_input IS NULL "
        "AND category IS NULL AND embedding IS NULL)",
    )
    op.create_index(
        "ix_memories_user_created",
        "memories",
        ["user_id", "created_at", "id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_memories_search_vector",
        "memories",
        ["search_vector"],
        postgresql_using="gin",
    )

    _lock_down("memories")


def downgrade() -> None:
    op.drop_table("memories")
    op.execute(sa.text("DROP TYPE IF EXISTS memory_category"))


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
