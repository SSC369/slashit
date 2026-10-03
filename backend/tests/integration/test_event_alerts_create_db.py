"""Epic 007, sub-plan 4.2, T-2.4 against a real database.

Creating an event through the wired events service sets one reminders row per
alert, through the real reminders adapter (C-1), and drops a passed lead from
the event (C-4). Extraction is skipped: the fields are what it would return.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core.context import Context
from app.core.db import user_transaction
from app.core.deps import build_event_service
from app.domains.events.public import EventDTO, EventFields

ALERT_ROWS = text(
    "SELECT next_fire_at, alert_detail, description FROM reminders "
    "WHERE event_id = :event_id AND deleted_at IS NULL ORDER BY next_fire_at"
)
EVENT_LEADS = text("SELECT alert_leads_minutes FROM calendar_events WHERE id = :id")


def _fields(*, start_date: date, leads: tuple[int, ...]) -> EventFields:
    return EventFields(
        title="Flight to Delhi",
        start_date=start_date,
        has_year=True,
        start_time=time(6),
        end_date=None,
        end_time=None,
        location=None,
        description=None,
        repeat_yearly=False,
        alert_leads_minutes=leads,
    )


async def _create(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    fields: EventFields,
) -> EventDTO:
    async with session_factory() as session:
        outcome = await build_event_service(
            Context(
                user_id=user_id,
                email=None,
                session=session,
                request_id="test",
                session_factory=session_factory,
            )
        ).create_event(
            user_id=user_id,
            fields=fields,
            origin="command",
            original_input="/add-event Flight to Delhi",
        )
    assert isinstance(outcome, EventDTO)
    return outcome


async def test_each_alert_becomes_one_reminders_row(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-1, FR-14, FR-18: two leads, two rows, each with its line."""
    user_a, _ = two_users
    start_date = datetime.now(UTC).date() + timedelta(days=20)

    event = await _create(
        session_factory,
        user_id=user_a,
        fields=_fields(start_date=start_date, leads=(1440, 10080)),
    )

    async with (
        session_factory() as session,
        user_transaction(session, user_a) as scoped,
    ):
        rows = (await scoped.execute(ALERT_ROWS, {"event_id": event.id})).all()
    assert [row.next_fire_at for row in rows] == [
        alert.fires_at for alert in event.alerts
    ]
    assert [row.alert_detail.split(" · ")[0] for row in rows] == [
        "1 week before",
        "1 day before",
    ]
    assert {row.description for row in rows} == {"Flight to Delhi"}


async def test_a_passed_lead_is_named_and_dropped_from_the_event(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-4, FR-19: the event keeps only the lead whose alert was set."""
    user_a, _ = two_users
    start_date = datetime.now(UTC).date() + timedelta(days=3)

    event = await _create(
        session_factory,
        user_id=user_a,
        fields=_fields(start_date=start_date, leads=(60, 20160)),
    )

    async with (
        session_factory() as session,
        user_transaction(session, user_a) as scoped,
    ):
        stored_leads = await scoped.scalar(EVENT_LEADS, {"id": event.id})
        rows = (await scoped.execute(ALERT_ROWS, {"event_id": event.id})).all()
        analytics = (
            await scoped.execute(
                text(
                    "SELECT event_type::text, properties FROM events "
                    "WHERE user_id = :user_id AND event_type IN "
                    "('event_created', 'event_alert_not_set') ORDER BY event_type"
                ),
                {"user_id": user_a},
            )
        ).all()
    assert [alert.text for alert in event.alerts_not_set] == ["2 weeks before"]
    assert [alert.reason for alert in event.alerts_not_set] == ["passed"]
    assert stored_leads == [60]
    assert len(rows) == 1
    # T-2.8, C-19: stored, and counts and booleans only (T6).
    assert [(row.event_type, row.properties) for row in analytics] == [
        ("event_alert_not_set", {"lead_minutes": 20160, "is_over_cap": False}),
        (
            "event_created",
            {
                "all_day": False,
                "has_end": False,
                "has_location": False,
                "yearly": False,
                "has_alert": True,
                "alert_count": 1,
            },
        ),
    ]
