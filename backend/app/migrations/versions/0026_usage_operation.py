"""ai_usage.operation: a generation or an embedding.

Revision ID: 0026_usage_operation
Revises: 0025_capture_memory
Create Date: 2026-09-25

Epic 004, sub-plan 4.1, build plan AD-11 and tech stack rule T9. Embedding
calls are recorded per user like every model call, but the per-user cap
counts generations only, so the allowance query needs to tell them apart.
Every existing row was a generation, which the default records.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0026_usage_operation"
down_revision: str | None = "0025_capture_memory"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

AI_OPERATIONS = ("generate", "embed")


def upgrade() -> None:
    op.execute(sa.text("CREATE TYPE ai_operation AS ENUM " + str(AI_OPERATIONS)))
    op.add_column(
        "ai_usage",
        sa.Column(
            "operation",
            postgresql.ENUM(*AI_OPERATIONS, name="ai_operation", create_type=False),
            nullable=False,
            server_default="generate",
        ),
    )


def downgrade() -> None:
    op.drop_column("ai_usage", "operation")
    op.execute(sa.text("DROP TYPE IF EXISTS ai_operation"))
