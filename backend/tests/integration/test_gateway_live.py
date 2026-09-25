"""End-to-end gateway cases against the real database and the real provider.

T-3.13 spends real money, a fraction of a cent per run. Per 04.3 question 4 it
runs locally and not in CI, so it skips when no key is configured rather than
failing a pipeline that has none.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_extract_interactor
from app.core.settings import Settings
from app.domains.gateway.interfaces.dtos import UsageRecord
from app.domains.gateway.public import Extraction, ExtractionRequest
from app.domains.gateway.repositories.usage_repository import SqlUsageRepository

TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "due": {"type": "string", "description": "ISO date if one is implied"},
    },
    "required": ["title"],
}


@pytest.mark.live
async def test_a_real_extraction_returns_a_result_and_records_it(
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-3.13: the whole gateway, against Gemini."""
    user_id, _ = two_users
    service = build_extract_interactor(
        session_factory=session_factory, settings=settings
    )

    result = await service.extract(
        user_id=user_id,
        request=ExtractionRequest(
            prompt="Finish the quarterly docs tomorrow",
            schema=TASK_SCHEMA,
            instruction="Extract the task. Today is 2026-09-12.",
        ),
    )

    assert isinstance(result, Extraction), f"got {type(result).__name__}: {result}"
    assert result.data.get("title"), "the model returned no title"
    assert result.input_tokens > 0, "token counts were not recorded"

    repository = SqlUsageRepository(session_factory)
    assert (
        await repository.count_since(
            user_id=user_id, since=_an_hour_ago(), operation="generate"
        )
        == 1
    )


async def test_usage_rows_are_isolated_between_users(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """T-3.14: the gateway's own rows obey the boundary slice 2 established."""
    user_a, user_b = two_users
    repository = SqlUsageRepository(session_factory)

    await repository.record(usage=_usage_for(user_a), occurred_at=datetime.now(UTC))

    assert (
        await repository.count_since(
            user_id=user_a, since=_an_hour_ago(), operation="generate"
        )
        == 1
    )
    assert (
        await repository.count_since(
            user_id=user_b, since=_an_hour_ago(), operation="generate"
        )
        == 0
    )


def _an_hour_ago() -> datetime:
    return datetime.now(UTC) - timedelta(hours=1)


def _usage_for(user_id: uuid.UUID) -> UsageRecord:
    return UsageRecord(
        id=uuid.uuid4(),
        user_id=user_id,
        provider="google",
        model="gemini-2.5-flash",
        input_tokens=10,
        output_tokens=5,
        outcome="success",
        latency_ms=120,
    )
