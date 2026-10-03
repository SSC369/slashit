"""Capture learns expenses: four questions, a typed draft, two outcomes.

Revision ID: 0040_capture_expense
Revises: 0039_expenses
Create Date: 2026-10-02

Epic 006, sub-plan 4.1, build plan AD-6. An unanswered expense question waits
in ``pending_captures`` with its draft in typed columns, so the database can
check what JSON could not. ``amount_candidates`` holds the numbers offered as
chips (FR-5). ``capture_turns`` gains ``resulting_expense_id`` and the outcomes
``expense_saved`` and ``expenses_summarised``; the latter is unused until
slice 2 and added now so slice 2 migrates nothing.

Not fully reversible: PostgreSQL cannot drop an enum value. Downgrade drops
the columns and leaves the enum values in place, unused.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0040_capture_expense"
down_revision: str | None = "0039_expenses"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

EXPENSE_MISSING_FIELDS = (
    "expense_amount",
    "expense_description",
    "expense_amount_choice",
    "expense_date",
)
EXPENSE_OUTCOMES = ("expense_saved", "expenses_summarised")


def upgrade() -> None:
    for missing_field in EXPENSE_MISSING_FIELDS:
        op.execute(
            sa.text(
                "ALTER TYPE pending_capture_missing_field "
                f"ADD VALUE IF NOT EXISTS '{missing_field}'"
            )
        )
    for outcome in EXPENSE_OUTCOMES:
        op.execute(
            sa.text(
                f"ALTER TYPE capture_turn_outcome ADD VALUE IF NOT EXISTS '{outcome}'"
            )
        )
    op.add_column(
        "pending_captures",
        sa.Column("expense_amount_paise", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "pending_captures", sa.Column("expense_description", sa.Text(), nullable=True)
    )
    # expense_category is created by 0039_expenses.
    op.add_column(
        "pending_captures",
        sa.Column(
            "expense_category",
            postgresql.ENUM(name="expense_category", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "pending_captures", sa.Column("expense_spent_on", sa.Date(), nullable=True)
    )
    op.add_column(
        "pending_captures",
        sa.Column(
            "amount_candidates", postgresql.ARRAY(sa.BigInteger()), nullable=True
        ),
    )
    op.create_check_constraint(
        "ck_pending_captures_expense_amount_positive",
        "pending_captures",
        "expense_amount_paise IS NULL OR expense_amount_paise > 0",
    )
    op.create_check_constraint(
        "ck_pending_captures_expense_description_length",
        "pending_captures",
        "expense_description IS NULL "
        "OR char_length(expense_description) BETWEEN 1 AND 200",
    )
    # No foreign key, for the reason 0006 gives resulting_task_id: this log
    # outlives the row it points at.
    op.add_column(
        "capture_turns", sa.Column("resulting_expense_id", sa.Uuid(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("capture_turns", "resulting_expense_id")
    op.drop_constraint(
        "ck_pending_captures_expense_description_length",
        "pending_captures",
        type_="check",
    )
    op.drop_constraint(
        "ck_pending_captures_expense_amount_positive",
        "pending_captures",
        type_="check",
    )
    for column in (
        "amount_candidates",
        "expense_spent_on",
        "expense_category",
        "expense_description",
        "expense_amount_paise",
    ):
        op.drop_column("pending_captures", column)
