"""Migration 0042_event_alerts, as the database holds it after `upgrade head`.

Epic 007, sub-plan 4.2, case C-18. The conversion of a stored lead, and the
lossy downgrade, were run by hand on the local database and are recorded in
the dev log, as slice 1's migrations were. These cases guard what slice 2's
code relies on.
"""

import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core.db import user_transaction

INSERT_EVENT = text(
    "INSERT INTO calendar_events (id, user_id, title, start_date, "
    "schedule_timezone, starts_at, ends_at, alert_leads_minutes, origin, "
    "created_at, updated_at) VALUES (:id, :user_id, 'Dentist', :start_date, "
    "'Asia/Kolkata', :now, :now, :leads, 'command', :now, :now)"
)


async def _insert_event_with_leads(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
    leads: list[int],
) -> uuid.UUID:
    event_id = uuid.uuid4()
    async with (
        session_factory() as session,
        user_transaction(session, user_id) as scoped,
    ):
        await scoped.execute(
            INSERT_EVENT,
            {
                "id": event_id,
                "user_id": user_id,
                "start_date": date(2026, 10, 9),
                "now": datetime.now(UTC),
                "leads": leads,
            },
        )
    return event_id


async def test_an_event_holds_many_leads_and_none_by_default(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    event_id = await _insert_event_with_leads(
        session_factory=session_factory, user_id=user_id, leads=[60, 1440]
    )
    async with (
        session_factory() as session,
        user_transaction(session, user_id) as scoped,
    ):
        stored_leads = await scoped.scalar(
            text("SELECT alert_leads_minutes FROM calendar_events WHERE id = :id"),
            {"id": event_id},
        )
        default_leads = await scoped.scalar(
            text(
                "SELECT column_default FROM information_schema.columns "
                "WHERE table_name = 'calendar_events' "
                "AND column_name = 'alert_leads_minutes'"
            )
        )

    assert stored_leads == [60, 1440]
    assert default_leads == "'{}'::integer[]"


@pytest.mark.parametrize("leads", [[-1], [60, 525601]])
async def test_a_lead_out_of_range_is_refused(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
    leads: list[int],
) -> None:
    user_id, _ = two_users
    with pytest.raises(IntegrityError, match="ck_event_alert_leads"):
        await _insert_event_with_leads(
            session_factory=session_factory, user_id=user_id, leads=leads
        )


async def test_alert_rows_and_event_alert_notifications_are_indexed(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        index_rows = (
            await session.execute(
                text(
                    "SELECT indexname, indexdef FROM pg_indexes WHERE indexname "
                    "IN ('ix_reminders_event', "
                    "'uq_notifications_event_alert_source')"
                )
            )
        ).all()
    index_definitions: dict[str, str] = {
        str(index_row.indexname): str(index_row.indexdef) for index_row in index_rows
    }

    assert "UNIQUE" not in index_definitions["ix_reminders_event"]
    assert "UNIQUE" in index_definitions["uq_notifications_event_alert_source"]
    assert (
        "action_target_id IS NOT NULL"
        in (index_definitions["uq_notifications_event_alert_source"])
    )


async def test_new_enum_values_exist(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        notification_kinds = (
            await session.scalars(
                text("SELECT unnest(enum_range(NULL::notification_kind))::text")
            )
        ).all()
        event_types = (
            await session.scalars(
                text("SELECT unnest(enum_range(NULL::event_type))::text")
            )
        ).all()

    assert "event_alert" in notification_kinds
    assert {"event_edited", "event_alert_not_set"} <= set(event_types)
