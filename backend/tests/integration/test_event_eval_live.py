"""Epic 007, sub-plan 4.1, T-1.13: NFR-2 and NFR-1 against the real model.

NFR-2 scores ``tests/eval/event_extraction.json`` field by field through the
same extraction call `/add-event` makes, with the clock fixed at the set's
reference moment so relative dates have one right answer. NFR-1 times
`/add-event` end to end through GraphQL. Spends a fraction of a cent per case.
Runs locally, never in CI, per the `live` marker's precedent (04.3 Q4).
"""

import json
import pathlib
import statistics
import uuid
from datetime import datetime, time
from time import perf_counter
from typing import Any, cast
from zoneinfo import ZoneInfo

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_extract_interactor
from app.core.settings import Settings
from app.domains.capture.adapters.gateway_extraction_adapter import (
    GatewayExtractionAdapter,
)
from app.domains.capture.constants import (
    EVENT_EXTRACTION_INSTRUCTION,
    EVENT_EXTRACTION_SCHEMA,
)
from app.domains.capture.services.event_capture import read_event_fields
from app.domains.gateway.public import Extraction
from tests.integration.test_memories_graphql import (
    _headers,
    _submit,
    patched_jwks,
    signing_key,
)

__all__ = ["patched_jwks", "signing_key"]

EVAL_SET = pathlib.Path(__file__).parent.parent / "eval" / "event_extraction.json"
TARGET_FIELD_ACCURACY = 0.90
TARGET_P95_SECONDS = 1.5
LATENCY_SAMPLES = 20
# What a field left out of a case's `expected` means: not said.
NOT_SAID: dict[str, Any] = {
    "start_date": None,
    "has_year": False,
    "start_time": None,
    "end_date": None,
    "end_time": None,
    "location": None,
    "repeat_yearly": False,
    "alert_leads_minutes": [],
}


class FixedClock:
    def __init__(self, *, moment: datetime, timezone_name: str) -> None:
        self.moment = moment
        self.timezone_name = timezone_name

    async def local_now(self, *, user_id: uuid.UUID) -> tuple[datetime, str]:
        return self.moment, self.timezone_name


def _observed(fields: Any) -> dict[str, Any]:
    if fields is None:
        return {"title": None, **NOT_SAID}
    start_date = fields.start_date.isoformat() if fields.start_date else None
    end_date = fields.end_date.isoformat() if fields.end_date else None
    return {
        "title": fields.title,
        "start_date": start_date,
        "has_year": fields.has_year,
        "start_time": _clock(fields.start_time),
        # A one-day event's end date says nothing the start date does not.
        "end_date": None if end_date == start_date else end_date,
        "end_time": _clock(fields.end_time),
        "location": fields.location.lower() if fields.location else None,
        "repeat_yearly": fields.repeat_yearly,
        "alert_leads_minutes": sorted(fields.alert_leads_minutes),
    }


def _clock(value: time | None) -> str | None:
    return value.strftime("%H:%M") if value else None


def _accepted(expected: dict[str, Any], field: str) -> list[Any]:
    value = expected.get(field, NOT_SAID.get(field))
    if isinstance(value, dict) and "any_of" in value:
        return list(value["any_of"])
    if field in ("title", "location") and isinstance(value, list):
        return value
    if field == "alert_leads_minutes":
        return [sorted(cast(list[int], value))]
    return [value]


@pytest.mark.live
async def test_field_accuracy_meets_nfr_2(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    eval_user: uuid.UUID,
) -> None:
    eval_set = json.loads(EVAL_SET.read_text())
    adapter = GatewayExtractionAdapter(
        extract_interactor=build_extract_interactor(
            session_factory=session_factory, settings=settings
        ),
        local_clock=FixedClock(
            moment=datetime.fromisoformat(eval_set["reference_moment"]).astimezone(
                ZoneInfo(eval_set["timezone"])
            ),
            timezone_name=eval_set["timezone"],
        ),
    )
    scored = 0
    misses: list[str] = []
    for case in eval_set["cases"]:
        result = await adapter.extract(
            user_id=eval_user,
            prompt=case["text"],
            schema=EVENT_EXTRACTION_SCHEMA,
            instruction=EVENT_EXTRACTION_INSTRUCTION,
        )
        assert isinstance(result, Extraction), result
        observed = _observed(
            read_event_fields(
                extracted_fields=cast(dict[str, Any], result.data), text=case["text"]
            )
        )
        for field, got in observed.items():
            scored += 1
            accepted = _accepted(case["expected"], field)
            if field == "title":
                accepted = [title.lower() for title in accepted]
                got = got.lower() if got else None
            if got not in accepted:
                misses.append(
                    f"{case['text']!r} {field}: expected {accepted}, got {got!r}"
                )

    accuracy = 1 - len(misses) / scored
    lines = len(eval_set["cases"])
    print(f"NFR-2 field accuracy {accuracy:.1%} over {scored} fields, {lines} lines")
    for miss in misses:
        print("  miss:", miss)
    assert accuracy > TARGET_FIELD_ACCURACY


@pytest.mark.live
@pytest.mark.usefixtures("patched_jwks")
async def test_capture_latency_meets_nfr_1(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    eval_user: uuid.UUID,
) -> None:
    lines = [case["text"] for case in json.loads(EVAL_SET.read_text())["cases"]]
    headers = _headers(signing_key, settings, user_id=eval_user)

    timings: list[float] = []
    outcomes: list[str] = []
    for line in lines[:LATENCY_SAMPLES]:
        started = perf_counter()
        result = await _submit(client, headers, f"/add-event {line}")
        timings.append(perf_counter() - started)
        outcomes.append(result["__typename"])

    p95 = statistics.quantiles(timings, n=20)[-1]
    print(
        f"NFR-1 /add-event p95 {p95:.2f} s, median {statistics.median(timings):.2f} s, "
        f"max {max(timings):.2f} s over {LATENCY_SAMPLES} captures"
    )
    print("outcomes:", {name: outcomes.count(name) for name in set(outcomes)})
    assert p95 < TARGET_P95_SECONDS
