"""Remove past `/forget` turns from capture history.

Revision ID: 0031_drop_forget_turns
Revises: 0030_forget_deletes
Create Date: 2026-09-27

Epic 004, sub-plan 4.5. Chat no longer has `/forget`; a memory is forgotten
from its detail page, which writes no capture turn. The user chose to delete
the "Forgot N memories" rows the command left. They held a count, never words.
The `memory_forgotten` outcome value stays: PostgreSQL cannot drop an enum value.

Not reversible: the rows are gone by the user's decision.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0031_drop_forget_turns"
down_revision: str | None = "0030_forget_deletes"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DELETE FROM capture_turns WHERE outcome = 'memory_forgotten'")


def downgrade() -> None:
    """Nothing to restore."""
