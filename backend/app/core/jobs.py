"""The Procrastinate app. One instance; every domain's ``jobs.py`` imports it
to register tasks against. See backend/.claude/rules/repo-rules.md section 14.

First wired for 002-authentication slice 1, task T-1.6: no domain used a
background job before this. The connector opens its own connection pool,
separate from the SQLAlchemy engine ``app/core/db.py`` builds for GraphQL
requests — Procrastinate's job-queue tables are not part of this codebase's
own schema, so it talks to Postgres through psycopg, not SQLAlchemy.

``import_paths`` is what lets the standalone ``procrastinate`` CLI (a worker
process run outside the FastAPI app) discover every domain's tasks without
this module importing them directly, which would be a cycle: a domain's
``jobs.py`` imports ``procrastinate_app`` from here to get the ``@task``
decorator, so this module cannot import the domain back. ``app/main.py``
additionally imports each domain's ``jobs.py`` once at startup, so periodic
tasks are registered before the in-process app ever calls ``open_async``.
"""

from procrastinate import App, PsycopgConnector

from app.core.settings import get_settings

_settings = get_settings()

# The queue's tables live in their own schema (migration 0020), so every
# connection the queue opens looks there first.
JOB_QUEUE_SEARCH_PATH = "-c search_path=procrastinate"

procrastinate_app = App(
    connector=PsycopgConnector(
        conninfo=_settings.database_url,
        kwargs={"options": JOB_QUEUE_SEARCH_PATH},
    ),
    import_paths=["app.domains.identity.jobs", "app.domains.reminders.jobs"],
)
