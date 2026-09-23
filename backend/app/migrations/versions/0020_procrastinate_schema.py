"""procrastinate: the job queue's own tables, in their own schema.

Revision ID: 0020_procrastinate_schema
Revises: 0019_firings_and_notifications
Create Date: 2026-09-23

Epic 003, sub-plan 4.2, T-2.8. No worker had run against this database
before: 002's purge job was registered but its queue tables were never
installed (002 dev log). Firing reminders needs a running worker (AD-9), so
the queue's schema lands here.

It goes into a ``procrastinate`` schema, not ``public``: Supabase exposes
``public`` through its data API, and the queue's rows (job arguments, locks)
are not user data for Row Level Security to police. ``app/core/jobs.py``
connects with ``search_path=procrastinate`` to match. The SQL is the one the
pinned Procrastinate release ships (``requirements.txt``); a version bump
applies that release's own migrations in a new revision.
"""

from collections.abc import Sequence
from importlib.resources import files

import sqlalchemy as sa
from alembic import op
from sqlalchemy.util import await_only

revision: str = "0020_procrastinate_schema"
down_revision: str | None = "0019_firings_and_notifications"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

JOB_QUEUE_SCHEMA = "procrastinate"


def upgrade() -> None:
    schema_sql = files("procrastinate.sql").joinpath("schema.sql").read_text()
    op.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {JOB_QUEUE_SCHEMA}"))
    op.execute(sa.text(f"SET LOCAL search_path TO {JOB_QUEUE_SCHEMA}"))
    # The file holds many statements and $$-quoted function bodies. asyncpg
    # only accepts that through its own execute(), the simple query protocol,
    # never through a prepared statement.
    driver_connection = op.get_bind().connection.driver_connection
    assert driver_connection is not None, "alembic runs on a live connection"
    await_only(driver_connection.execute(schema_sql))
    op.execute(sa.text("SET LOCAL search_path TO public"))


def downgrade() -> None:
    op.execute(sa.text(f"DROP SCHEMA IF EXISTS {JOB_QUEUE_SCHEMA} CASCADE"))
