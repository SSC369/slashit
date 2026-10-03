"""expenses: one spend per row, in integer paise, on a local calendar date.

Revision ID: 0039_expenses
Revises: 0038_capture_events
Create Date: 2026-10-02

Epic 006, sub-plan 4.1. Money is ``bigint`` paise and never a float or a
decimal (build plan AD-2). ``spent_on`` is a ``date`` in the user's zone, not a
timestamp, so "yesterday" at 11 pm and a month's total read the same day
(AD-3). Soft-deleted, as tasks and reminders are.

The search columns ship here, empty until slice 3's embed job fills them, so
the table's shape is fixed from the first row (index, table of migrations).

Rule T2: Row Level Security is enabled, forced, and given a policy in the
same migration that creates the table.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0039_expenses"
down_revision: str | None = "0038_capture_events"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

EXPENSE_CATEGORIES = (
    "food",
    "transport",
    "shopping",
    "bills",
    "health",
    "entertainment",
    "travel",
    "other",
)
EMBEDDING_DIMENSIONS = 768


def upgrade() -> None:
    op.execute(
        sa.text("CREATE TYPE expense_category AS ENUM " + str(EXPENSE_CATEGORIES))
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "category",
            postgresql.ENUM(
                *EXPENSE_CATEGORIES, name="expense_category", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("spent_on", sa.Date(), nullable=False),
        # record_origin already exists, created by 0003_tasks.
        sa.Column(
            "origin",
            postgresql.ENUM(name="record_origin", create_type=False),
            nullable=False,
        ),
        sa.Column("original_input", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("amount_paise > 0", name="ck_expenses_amount_positive"),
        sa.CheckConstraint(
            "char_length(description) BETWEEN 1 AND 200",
            name="ck_expenses_description_length",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], ondelete="CASCADE"),
    )
    # Added by SQL because SQLAlchemy core has no vector or generated tsvector
    # column type without the ORM model, as in 0024_memories.
    op.execute(
        sa.text(
            f"ALTER TABLE expenses ADD COLUMN embedding vector({EMBEDDING_DIMENSIONS})"
        )
    )
    # The category is spelled out so "food" finds every food spend by words
    # (PRD FR-29). A CASE, not ``category::text``: an enum's text output is only
    # STABLE, and a generated column needs an IMMUTABLE expression.
    category_words = " ".join(
        f"WHEN '{category}' THEN '{category}'" for category in EXPENSE_CATEGORIES
    )
    op.execute(
        sa.text(
            "ALTER TABLE expenses ADD COLUMN search_vector tsvector "
            "GENERATED ALWAYS AS (to_tsvector('english', description || ' ' || "
            f"CASE category {category_words} END)) STORED"
        )
    )
    # The list and slice 2's summary both read by user among live rows,
    # newest spend first.
    op.create_index(
        "ix_expenses_user_spent_on",
        "expenses",
        ["user_id", sa.text("spent_on DESC")],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_expenses_search_vector",
        "expenses",
        ["search_vector"],
        postgresql_using="gin",
    )

    _lock_down("expenses")


def downgrade() -> None:
    op.drop_table("expenses")
    op.execute(sa.text("DROP TYPE IF EXISTS expense_category"))


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
