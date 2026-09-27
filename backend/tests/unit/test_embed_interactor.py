"""EmbedInteractor, sub-plan 4.1 case C-11 and tech stack rule T9."""

import uuid

import pytest

from app.core.settings import Settings, get_settings
from app.domains.gateway.errors import (
    ProviderTimeout,
    ProviderTimeoutError,
    ProviderUnavailable,
    ProviderUnavailableError,
    SharedQuotaExhausted,
    SharedQuotaExhaustedError,
)
from app.domains.gateway.interactors.embed import EmbedInteractor
from app.domains.gateway.interfaces.dtos import Embedding
from app.domains.gateway.services.allowance_service import AllowanceService
from tests.fakes.fake_provider import FakeProvider
from tests.fakes.fake_usage_repository import FakeUsageRepository


def _interactor(
    *,
    provider: FakeProvider,
    usage: FakeUsageRepository,
    settings: Settings | None = None,
) -> EmbedInteractor:
    return EmbedInteractor(
        provider=provider, usage_repository=usage, settings=settings or get_settings()
    )


async def test_an_embed_records_one_embed_row_and_never_checks_the_cap() -> None:
    """C-11, T9: a user at their cap may still embed, and it is attributed."""
    usage = FakeUsageRepository(limit=20, used=20)
    interactor = _interactor(provider=FakeProvider(), usage=usage)

    result = await interactor.embed(user_id=uuid.uuid4(), text="a fact")

    assert isinstance(result, Embedding)
    assert len(result.vector) == 768
    assert [row.operation for row in usage.records] == ["embed"]
    assert usage.outcomes == ["success"]
    assert usage.counted_operations == []


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (ProviderUnavailableError(), ProviderUnavailable),
        (ProviderTimeoutError(3.0), ProviderTimeout),
        (SharedQuotaExhaustedError(), SharedQuotaExhausted),
    ],
)
async def test_each_failure_is_returned_and_recorded(
    raised: Exception, expected: type
) -> None:
    usage = FakeUsageRepository()
    interactor = _interactor(provider=FakeProvider(raises=raised), usage=usage)

    result = await interactor.embed(user_id=uuid.uuid4(), text="a fact")

    assert isinstance(result, expected)
    assert len(usage.records) == 1
    assert usage.records[0].operation == "embed"


async def test_the_kill_switch_refuses_without_calling_or_recording() -> None:
    usage = FakeUsageRepository()
    provider = FakeProvider()
    settings = get_settings().model_copy(update={"gateway_enabled": False})
    interactor = _interactor(provider=provider, usage=usage, settings=settings)

    result = await interactor.embed(user_id=uuid.uuid4(), text="a fact")

    assert isinstance(result, ProviderUnavailable)
    assert provider.calls == 0
    assert usage.records == []


async def test_the_allowance_counts_generations_only() -> None:
    """T9: AllowanceService asks storage for generate rows, never embed ones."""
    usage = FakeUsageRepository(limit=20, used=3)

    await AllowanceService(usage).allowance_for(user_id=uuid.uuid4())

    assert usage.counted_operations == ["generate"]
