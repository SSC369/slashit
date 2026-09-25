"""pgvector: the extension memories' meaning vectors need.

Revision ID: 0023_pgvector
Revises: 0022_notifications_soft_delete
Create Date: 2026-09-25

Epic 004, sub-plan 4.1, build plan AD-4. Created in the default schema, so the
``vector`` type and the ``<=>`` operator resolve without a schema prefix on
both Supabase and a local database. Supabase offers the extension; this
enables it.

Downgrade drops the extension only if nothing uses it, which is the case once
0024 is downgraded first.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0023_pgvector"
down_revision: str | None = "0022_notifications_soft_delete"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))


def downgrade() -> None:
    op.execute(sa.text("DROP EXTENSION IF EXISTS vector"))
