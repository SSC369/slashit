"""Epic 007, sub-plan 4.2, T-2.7: C-16 and C-17 for search, against
PostgreSQL with only the model faked. Events found by title, location and
description words and by meaning, filtered on the Events tab, related on
detail; a deleted event and another user's never."""

import uuid
from datetime import UTC, datetime, time, timedelta
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.context import Context
from app.core.deps import build_event_service
from app.core.settings import Settings
from app.domains.events.interfaces.dtos import EventText
from app.domains.events.public import EventDTO, EventFields
from app.domains.events.repositories.calendar_event_repository import (
    SqlCalendarEventRepository,
)
from tests.integration.search_harness import (
    auth_headers,
    embed_text,
    graphql,
    keyword_embedder,
    patched_jwks,
    signing_key,
)

__all__ = ["keyword_embedder", "patched_jwks", "signing_key"]

SUBMIT = """
mutation($rawInput: String!) {
  submitCapture(rawInput: $rawInput) {
    __typename
    ... on SearchResults {
      groups { recordType hits { record { __typename ... on Event { id } } } }
    }
  }
}
"""
SEARCH = """
query($text: String!, $recordType: RecordType) {
  search(text: $text, recordType: $recordType, offset: 0, limit: 50) {
    ... on SearchPage { total hits { __typename ... on Event { id } } }
  }
}
"""
RELATED = """
query($id: ID!) {
  relatedRecords(recordType: EVENT, id: $id) { __typename ... on Event { id } }
}
"""


async def _seed(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
    *,
    title: str,
    location: str | None = None,
    description: str | None = None,
    meaning: str | None = None,
) -> EventDTO:
    async with session_factory() as session:
        event = await build_event_service(
            Context(
                user_id=user_id,
                email=None,
                session=session,
                request_id="test",
                session_factory=session_factory,
            )
        ).create_event(
            user_id=user_id,
            fields=EventFields(
                title=title,
                start_date=datetime.now(UTC).date() + timedelta(days=10),
                has_year=True,
                start_time=time(16),
                end_date=None,
                end_time=None,
                location=location,
                description=description,
                repeat_yearly=False,
                alert_leads_minutes=(),
            ),
            origin="command",
            original_input=None,
        )
    assert isinstance(event, EventDTO)
    if meaning is not None:
        async with session_factory() as session:
            await SqlCalendarEventRepository(session).set_embedding(
                user_id=user_id,
                event_id=event.id,
                words=EventText(
                    title=title, location=location, description=description
                ),
                embedding=embed_text(meaning),
            )
    return event


async def _event_hits(
    client: AsyncClient, headers: dict[str, str], line: str
) -> list[str]:
    data = await graphql(client, headers, SUBMIT, {"rawInput": line})
    return [
        hit["record"]["id"]
        for group in data["submitCapture"]["groups"]
        if group["recordType"] == "EVENT"
        for hit in group["hits"]
    ]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_words_find_events_by_title_location_and_description(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-16, FR-30: and a deleted event is never found."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)
    dentist = await _seed(
        session_factory,
        user_id,
        title="Dentist",
        location="Apollo Clinic",
        description="Bring the old X-rays",
    )
    gone = await _seed(session_factory, user_id, title="Dentist follow-up")
    async with session_factory() as session:
        await SqlCalendarEventRepository(session).soft_delete(
            user_id=user_id, event_id=gone.id
        )

    assert await _event_hits(client, headers, "/search dentist") == [str(dentist.id)]
    assert await _event_hits(client, headers, "/search apollo") == [str(dentist.id)]
    assert await _event_hits(client, headers, "/search x-rays") == [str(dentist.id)]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_meaning_finds_an_event_and_its_detail_lists_related(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """005 FR-5 and FR-25 for events: "visa" finds the embassy appointment."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)
    embassy = await _seed(
        session_factory, user_id, title="Embassy appointment", meaning="passport"
    )
    photos = await _seed(
        session_factory, user_id, title="Photo studio", meaning="passport"
    )

    found = await _event_hits(client, headers, "/search visa")
    related = await graphql(client, headers, RELATED, {"id": str(embassy.id)})

    assert sorted(found) == sorted([str(embassy.id), str(photos.id)])
    assert related["relatedRecords"] == [{"__typename": "Event", "id": str(photos.id)}]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_records_search_filters_to_events(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """005 FR-22: the Events tab's box sends EVENT (dev log D-6)."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)
    dentist = await _seed(session_factory, user_id, title="Dentist")

    data = await graphql(
        client, headers, SEARCH, {"text": "dentist", "recordType": "EVENT"}
    )

    page: dict[str, Any] = data["search"]
    assert page["total"] == 1
    assert page["hits"] == [{"__typename": "Event", "id": str(dentist.id)}]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_another_users_event_is_never_found_or_related(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-17, NFR-6, rule T7."""
    user_a, user_b = two_users
    event = await _seed(session_factory, user_a, title="Dentist", meaning="passport")
    headers_b = auth_headers(signing_key, settings, user_id=user_b)

    assert await _event_hits(client, headers_b, "/search dentist") == []
    related = await graphql(client, headers_b, RELATED, {"id": str(event.id)})
    assert related["relatedRecords"] == []
