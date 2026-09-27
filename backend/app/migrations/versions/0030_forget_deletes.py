"""Forget deletes: remove the traces earlier forgets left.

Revision ID: 0030_forget_deletes
Revises: 0029_memory_conflicts
Create Date: 2026-09-27

Epic 004, sub-plan 4.4 (build plan AD-2, amended 2026-09-27). Forget now
deletes the memory row and its thread's capture turns. Rows forgotten before
this change stayed as an empty tombstone and blanked turns; this removes them.
The `deleted_at` and `forgotten_at` columns and their checks stay, unused.

Not reversible: the removed rows held no words, and forget means gone.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0030_forget_deletes"
down_revision: str | None = "0029_memory_conflicts"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DELETE FROM capture_turns WHERE forgotten_at IS NOT NULL")
    op.execute("DELETE FROM memories WHERE deleted_at IS NOT NULL")


def downgrade() -> None:
    """Nothing to restore: the deleted rows were already empty."""
