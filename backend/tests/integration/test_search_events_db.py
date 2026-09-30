"""Epic 005, sub-plan 4.2, C-2.11: event properties are numbers only, in the
database itself, and `recordSearchEvent` stores a position (PRD section 8, T6)."""

import uuid
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.settings import Settings
from app.domains.analytics.models import Event
from tests.integration.search_harness import (
    auth_headers,
    graphql,
    patched_jwks,
    signing_key,
)

__all__ = ["patched_jwks", "signing_key"]

RECORD = """
mutation($input: RecordSearchEventInput!) { recordSearchEvent(input: $input) }
"""


@pytest.mark.parametrize(
    "properties",
    ['{"query": "passport"}', '{"nested": {"a": 1}}', '{"list": [1, 2]}', "[1]"],
)
async def test_the_database_refuses_anything_but_numbers(
    engine: AsyncEngine, two_users: tuple[uuid.UUID, uuid.UUID], properties: str
) -> None:
    user_id, _ = two_users
    with pytest.raises(IntegrityError):
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "INSERT INTO events (id, user_id, event_type, occurred_at, "
                    "properties) VALUES (:id, :user_id, 'search_run', :at, "
                    "CAST(:properties AS jsonb))"
                ),
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "at": datetime.now(UTC),
                    "properties": properties,
                },
            )


async def test_numbers_and_booleans_are_accepted(
    engine: AsyncEngine, two_users: tuple[uuid.UUID, uuid.UUID]
) -> None:
    user_id, _ = two_users
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO events (id, user_id, event_type, occurred_at, "
                "properties) VALUES (:id, :user_id, 'search_run', :at, "
                "CAST(:properties AS jsonb))"
            ),
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "at": datetime.now(UTC),
                "properties": '{"result_count": 3, "answered": true, "ratio": 0.5}',
            },
        )


async def test_an_event_without_properties_stores_sql_null(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """A JSON `null` is not an object, so the check would refuse it: every
    event before 005 would fail to write."""
    user_id, _ = two_users
    async with session_factory() as session, session.begin():
        session.add(
            Event(
                id=uuid.uuid4(),
                user_id=user_id,
                event_type="records_view_opened",
                occurred_at=datetime.now(UTC),
                properties=None,
            )
        )
    async with session_factory() as session:
        stored_as_null = (
            await session.execute(
                text("SELECT properties IS NULL FROM events WHERE user_id = :user_id"),
                {"user_id": user_id},
            )
        ).scalar_one()
    assert stored_as_null is True


@pytest.mark.usefixtures("patched_jwks")
async def test_an_opened_result_is_recorded_with_its_position(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)

    await graphql(
        client,
        headers,
        RECORD,
        {"input": {"kind": "SEARCH_RESULT_OPENED", "position": 3}},
    )
    await graphql(
        client,
        headers,
        RECORD,
        {"input": {"kind": "ANSWER_CITATION_OPENED", "position": 1}},
    )

    async with session_factory() as session:
        rows = (
            await session.execute(
                select(Event.event_type, Event.properties).where(
                    Event.user_id == user_id
                )
            )
        ).all()
    assert sorted((row[0], row[1]) for row in rows) == [
        ("answer_citation_opened", {"citation": 1}),
        ("search_result_opened", {"position": 3}),
    ]
