"""Event alerts: any number per event, each a one-time reminder row.

Revision ID: 0042_event_alerts
Revises: 0041_expense_events
Create Date: 2026-10-03

Epic 007, sub-plan 4.2, task T-2.1. An event may carry any number of alerts
(dev log X-1; build plan AD-3, AD-8).

- ``calendar_events.alert_lead_minutes`` becomes ``alert_leads_minutes``, a
  distinct, ascending ``integer[]``. Slice 1's single stored lead is copied
  into a one-element list. ``calendar_events.alerts_pending`` is true from
  the moment an event's alerts must change until reminders holds the new
  set; the 15-minute sweep re-arms any event left true (4.2 Q1, dev log
  D-20).
- ``reminders.event_id`` links an alert row to its event. Many rows per
  event, so the index is not unique. ``reminders.alert_detail`` is the line
  the alert's notification shows under the event title, such as "1 day
  before · Mon 12 Oct, all day", written by events when it sets the alert:
  reminders knows neither the lead nor the event's date (dev log D-18).
- ``notification_kind`` gains ``event_alert``. ``notifications`` gains
  ``action_target_id``: the alert's reminder row, which Done and Snooze act
  on, while ``target_id`` stays the event that Open goes to (build plan AD-5,
  4.2 Q2). Event alerts get their own one-row-per-firing index, as reminders
  have (003 AD-3). Its predicate is ``action_target_id IS NOT NULL``, which
  only event alerts set: a value added to an enum cannot be used in the
  transaction that adds it, and a cast to text is not immutable.
- Analytics ``event_type`` gains ``event_edited`` and ``event_alert_not_set``
  (dev log D-10).

Downgrade loses data: each event keeps only its first lead, the shortest,
since a single column cannot hold more. Accepted by the user on 2026-10-03
(implementation plan index §5). Enum values stay, as PostgreSQL cannot drop
them.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0042_event_alerts"
down_revision: str | None = "0041_expense_events"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

MAX_ALERT_LEAD_MINUTES = 525600
ANALYTICS_EVENT_TYPES = ("event_edited", "event_alert_not_set")


def upgrade() -> None:
    _convert_event_leads_to_list()
    _link_reminders_to_events()
    _add_event_alert_notifications()
    for event_type in ANALYTICS_EVENT_TYPES:
        op.execute(
            sa.text(f"ALTER TYPE event_type ADD VALUE IF NOT EXISTS '{event_type}'")
        )


def downgrade() -> None:
    op.drop_index("ix_calendar_events_alerts_pending", table_name="calendar_events")
    op.drop_column("calendar_events", "alerts_pending")
    op.drop_index("uq_notifications_event_alert_source", table_name="notifications")
    op.drop_column("notifications", "action_target_id")
    op.drop_index("ix_reminders_event", table_name="reminders")
    op.drop_column("reminders", "alert_detail")
    op.drop_column("reminders", "event_id")
    _restore_single_event_lead()


def _convert_event_leads_to_list() -> None:
    op.add_column(
        "calendar_events",
        sa.Column(
            "alert_leads_minutes",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default=sa.text("'{}'::integer[]"),
        ),
    )
    op.execute(
        sa.text(
            "UPDATE calendar_events SET alert_leads_minutes = "
            "ARRAY[alert_lead_minutes] WHERE alert_lead_minutes IS NOT NULL"
        )
    )
    op.drop_constraint("ck_event_alert_lead", "calendar_events", type_="check")
    op.drop_column("calendar_events", "alert_lead_minutes")
    op.create_check_constraint(
        "ck_event_alert_leads",
        "calendar_events",
        f"0 <= ALL (alert_leads_minutes) "
        f"AND {MAX_ALERT_LEAD_MINUTES} >= ALL (alert_leads_minutes)",
    )
    op.add_column(
        "calendar_events",
        sa.Column(
            "alerts_pending",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # The sweep reads only the few events left pending.
    op.create_index(
        "ix_calendar_events_alerts_pending",
        "calendar_events",
        ["updated_at"],
        postgresql_where=sa.text("alerts_pending AND deleted_at IS NULL"),
    )


def _link_reminders_to_events() -> None:
    op.add_column("reminders", sa.Column("event_id", sa.Uuid(), nullable=True))
    op.add_column("reminders", sa.Column("alert_detail", sa.Text(), nullable=True))
    op.create_foreign_key(
        "fk_reminders_event",
        "reminders",
        "calendar_events",
        ["event_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # set_event_alerts replaces an event's live rows; this finds them.
    op.create_index(
        "ix_reminders_event",
        "reminders",
        ["event_id"],
        postgresql_where=sa.text("event_id IS NOT NULL AND deleted_at IS NULL"),
    )


def _add_event_alert_notifications() -> None:
    op.execute(
        sa.text("ALTER TYPE notification_kind ADD VALUE IF NOT EXISTS 'event_alert'")
    )
    op.add_column(
        "notifications", sa.Column("action_target_id", sa.Uuid(), nullable=True)
    )
    op.create_index(
        "uq_notifications_event_alert_source",
        "notifications",
        ["source_id"],
        unique=True,
        postgresql_where=sa.text("action_target_id IS NOT NULL"),
    )


def _restore_single_event_lead() -> None:
    op.add_column(
        "calendar_events",
        sa.Column("alert_lead_minutes", sa.Integer(), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE calendar_events SET alert_lead_minutes = alert_leads_minutes[1] "
            "WHERE cardinality(alert_leads_minutes) > 0"
        )
    )
    op.drop_constraint("ck_event_alert_leads", "calendar_events", type_="check")
    op.drop_column("calendar_events", "alert_leads_minutes")
    op.create_check_constraint(
        "ck_event_alert_lead",
        "calendar_events",
        f"alert_lead_minutes IS NULL OR alert_lead_minutes "
        f"BETWEEN 0 AND {MAX_ALERT_LEAD_MINUTES}",
    )
