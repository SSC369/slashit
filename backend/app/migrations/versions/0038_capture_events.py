"""Capture learns events: two questions, two outcomes, one turn link.

Revision ID: 0038_capture_events
Revises: 0037_calendar_events
Create Date: 2026-10-02

Epic 007, sub-plan 4.1. ``pending_captures`` gains the missing fields
``event_date`` (FR-2) and ``event_alert_choice`` (FR-16). ``capture_turns``
gains the outcomes ``event_created`` and ``events_listed`` and a
``resulting_event_id``, with no foreign key, as for every other resulting id.
Analytics gains ``event_created``, whose properties are booleans only (T6).

Not fully reversible: PostgreSQL cannot drop an enum value.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0038_capture_events"
down_revision: str | None = "0037_calendar_events"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    for missing_field in ("event_date", "event_alert_choice"):
        op.execute(
            sa.text(
                "ALTER TYPE pending_capture_missing_field "
                f"ADD VALUE IF NOT EXISTS '{missing_field}'"
            )
        )
    for outcome in ("event_created", "events_listed"):
        op.execute(
            sa.text(
                f"ALTER TYPE capture_turn_outcome ADD VALUE IF NOT EXISTS '{outcome}'"
            )
        )
    op.execute(sa.text("ALTER TYPE event_type ADD VALUE IF NOT EXISTS 'event_created'"))
    op.add_column(
        "capture_turns", sa.Column("resulting_event_id", sa.Uuid(), nullable=True)
    )


def downgrade() -> None:
    """The column goes; the enum values stay, unused."""
    op.drop_column("capture_turns", "resulting_event_id")
