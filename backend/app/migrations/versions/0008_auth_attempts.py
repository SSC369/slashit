"""auth_attempts: rate-limit state for sign-in and signup, read and written
only by Supabase's Auth Hooks.

Revision ID: 0008_auth_attempts
Revises: 0007_profiles
Create Date: 2026-09-14

FR-17, FR-19. One row per (subject, kind): `subject` is a user id for
`sign_in` attempts (the hook is only invoked once Supabase already knows
which user is authenticating) and an email for `signup` attempts (there is
no user yet). The unique index on (subject, kind) is what lets both hook
functions in 0009_auth_hooks.py do a single upsert-shaped read.

Rule T2: Row Level Security is enabled and forced in the same migration
that creates the table. Unlike every other table in this schema, no grant
goes to `authenticated` or `anon` — nothing here is ever read on a caller's
own behalf, only by the hook functions Supabase Auth invokes as
`supabase_auth_admin`. `FORCE ROW LEVEL SECURITY` blocks every role,
`supabase_auth_admin` included, until a policy admits it: that role is not
documented to carry `BYPASSRLS`, so rather than assume it does, this
migration grants it table privileges and an explicit permissive policy.
That is the standard, conservative shape for a hooks-only table and is the
safest choice available without a live project to check the role's actual
attributes against.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_auth_attempts"
down_revision: str | None = "0007_profiles"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_attempts",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_started_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("locked_until", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "kind IN ('sign_in', 'signup')", name="ck_auth_attempts_kind"
        ),
    )
    op.create_index(
        "ux_auth_attempts_subject_kind",
        "auth_attempts",
        ["subject", "kind"],
        unique=True,
    )

    _lock_down()


def downgrade() -> None:
    op.drop_table("auth_attempts")


def _lock_down() -> None:
    op.execute(sa.text("ALTER TABLE auth_attempts ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE auth_attempts FORCE ROW LEVEL SECURITY"))
    op.execute(
        sa.text("GRANT SELECT, INSERT, UPDATE ON auth_attempts TO supabase_auth_admin")
    )
    op.execute(
        sa.text(
            "CREATE POLICY auth_attempts_service_only ON auth_attempts FOR ALL "
            "TO supabase_auth_admin USING (true) WITH CHECK (true)"
        )
    )
