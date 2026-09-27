"""Orchestration cases. See 04.3 section 8.

The point of these is step three of `extract`: every path that reached the
provider writes exactly one usage row. FR-13, and the step most easily skipped
on an error branch.
"""

import dataclasses
import uuid

import pytest

from app.core.settings import Settings, get_settings
from app.domains.gateway.errors import (
    Extraction,
    MalformedResult,
    MalformedResultError,
    ProviderTimeout,
    ProviderTimeoutError,
    ProviderUnavailable,
    ProviderUnavailableError,
    SharedQuotaExhausted,
    SharedQuotaExhaustedError,
    UserLimitReached,
)
from app.domains.gateway.interactors.extract import ExtractInteractor
from app.domains.gateway.interfaces.dtos import (
    ExtractionRequest,
    ProviderResult,
    UsageRecord,
)
from app.domains.gateway.services.allowance_service import AllowanceService
from tests.fakes.fake_provider import FakeProvider
from tests.fakes.fake_usage_repository import FakeUsageRepository

REQUEST = ExtractionRequest(prompt="finish docs tomorrow", schema={"type": "object"})
SUCCESS = ProviderResult(
    data={"title": "finish docs"},
    input_tokens=500,
    output_tokens=150,
    model="gemini-2.5-flash",
)


def _service(
    provider: FakeProvider, repo: FakeUsageRepository, settings: Settings | None = None
) -> ExtractInteractor:
    settings = settings or get_settings()
    return ExtractInteractor(
        provider=provider,
        usage_repository=repo,
        allowance_service=AllowanceService(repo),
        settings=settings,
    )


async def test_success_returns_extraction_and_records_one_row() -> None:
    repo = FakeUsageRepository(limit=20, used=0)
    provider = FakeProvider(result=SUCCESS)

    result = await _service(provider, repo).extract(
        user_id=uuid.uuid4(), request=REQUEST
    )

    assert isinstance(result, Extraction)
    assert result.input_tokens == 500
    assert repo.outcomes == ["success"]


async def test_user_at_limit_is_refused_without_calling_the_provider() -> None:
    """T-3.1: FR-8 says the check runs before the call, so it costs nothing."""
    repo = FakeUsageRepository(limit=20, used=20)
    provider = FakeProvider(result=SUCCESS)

    result = await _service(provider, repo).extract(
        user_id=uuid.uuid4(), request=REQUEST
    )

    assert isinstance(result, UserLimitReached)
    assert provider.calls == 0, "the provider was called despite the user being over"
    assert repo.outcomes == ["user_limit_reached"]


async def test_refusal_carries_the_limit_and_a_reset_time() -> None:
    """T-3.4: FR-9."""
    repo = FakeUsageRepository(limit=7, used=7)

    result = await _service(FakeProvider(result=SUCCESS), repo).extract(
        user_id=uuid.uuid4(), request=REQUEST
    )

    assert isinstance(result, UserLimitReached)
    assert result.limit == 7
    assert result.resets_at is not None


@pytest.mark.parametrize(
    ("raised", "expected_type", "expected_outcome"),
    [
        (SharedQuotaExhaustedError(), SharedQuotaExhausted, "shared_quota_exhausted"),
        (ProviderUnavailableError(), ProviderUnavailable, "provider_unavailable"),
        (ProviderTimeoutError(8.0), ProviderTimeout, "provider_timeout"),
        (MalformedResultError("bad shape"), MalformedResult, "malformed_result"),
    ],
)
async def test_each_provider_failure_maps_and_records(
    raised: Exception, expected_type: type, expected_outcome: str
) -> None:
    """T-3.5, T-3.6: six outcomes, each distinct, each recorded exactly once."""
    repo = FakeUsageRepository(limit=20, used=0)

    result = await _service(FakeProvider(raises=raised), repo).extract(
        user_id=uuid.uuid4(), request=REQUEST
    )

    assert isinstance(result, expected_type)
    assert repo.outcomes == [expected_outcome], "expected exactly one row"


async def test_kill_switch_refuses_without_calling_the_provider() -> None:
    """T-3.11: GATEWAY_ENABLED=false, one variable, no deploy."""
    repo = FakeUsageRepository(limit=20, used=0)
    provider = FakeProvider(result=SUCCESS)
    disabled = get_settings().model_copy(update={"gateway_enabled": False})

    result = await _service(provider, repo, disabled).extract(
        user_id=uuid.uuid4(), request=REQUEST
    )

    assert isinstance(result, ProviderUnavailable)
    assert provider.calls == 0


async def test_kill_switch_does_not_consume_the_users_daily_count() -> None:
    """A disabled gateway is our fault, so it must not cost the user a call."""
    repo = FakeUsageRepository(limit=20, used=0)
    disabled = get_settings().model_copy(update={"gateway_enabled": False})

    await _service(FakeProvider(result=SUCCESS), repo, disabled).extract(
        user_id=uuid.uuid4(), request=REQUEST
    )

    assert repo.records == []


async def test_a_failed_usage_write_still_returns_the_result() -> None:
    """The caller paid for this result; a bookkeeping failure must not eat it.

    FR-15 forbids losing usage silently, not losing it at all. The loss is
    logged at error and surfaces in NFR-3's reconciliation.
    """
    repo = FakeUsageRepository(limit=20, used=0)
    repo.record_should_fail = True

    result = await _service(FakeProvider(result=SUCCESS), repo).extract(
        user_id=uuid.uuid4(), request=REQUEST
    )

    assert isinstance(result, Extraction)


def test_usage_row_holds_no_user_text() -> None:
    """T-3.10: FR-12, asserted against the fields, not the values.

    Checking values would pass for a row that happens to be empty. Checking the
    shape fails the day someone adds a column that could hold a passport number.
    """
    allowed = {
        "id",
        "user_id",
        "provider",
        "model",
        "input_tokens",
        "output_tokens",
        "outcome",
        "latency_ms",
        # Epic 004: "generate" or "embed", an enum that cannot hold text.
        "operation",
    }

    actual = {f.name for f in dataclasses.fields(UsageRecord)}

    assert actual == allowed, (
        f"UsageRecord gained or lost a field: {actual ^ allowed}. "
        "FR-12 forbids prompt or response content reaching ai_usage."
    )
