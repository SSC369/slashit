"""Epic 006, sub-plan 4.2, C-31: NFR-3 at 5,000 expenses, through GraphQL.
Seeds a year of rows directly; no model is called. Runs locally, never in CI
(`slow`). From a dev machine this measures the local database; epic 012
re-measures from the deployed API."""

import random
import statistics
import time
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from app.domains.expenses.interfaces.dtos import ExpenseCategory
from app.domains.expenses.models import Expense
from tests.integration.expense_harness import (
    auth_headers,
    graphql,
    patched_jwks,
    signing_key,
)

__all__ = ["patched_jwks", "signing_key"]

pytestmark = pytest.mark.slow

EXPENSE_COUNT = 5_000
RUNS = 50
TARGET_P95_SECONDS = 1.0

PERIODS = "query { expensePeriods { key start end } }"
SUMMARY = """
query($filter: ExpensesFilterInput) {
  expenseSummary(filter: $filter) {
    count grandTotalPaise totals { category totalPaise }
  }
}
"""
LIST = """
query($filter: ExpensesFilterInput) { expenses(filter: $filter) { id amountPaise } }
"""


async def _seed(
    *, session_factory: async_sessionmaker[AsyncSession], user_id: uuid.UUID
) -> None:
    """Five thousand expenses spread over the last 365 days, as the PRD's
    estimate of five a day for three years, compressed into one."""
    generator = random.Random(6)
    today = date.today()
    now = datetime.now(UTC)
    categories = list(ExpenseCategory)
    rows = [
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "amount_paise": generator.randint(1_000, 500_000),
            "description": f"spend {index}",
            "category": generator.choice(categories).value,
            "spent_on": today - timedelta(days=generator.randint(0, 364)),
            "origin": "command",
            "original_input": f"/add-expense spend {index}",
            "created_at": now,
            "updated_at": now,
        }
        for index in range(EXPENSE_COUNT)
    ]
    async with session_factory() as session, session.begin():
        await session.execute(insert(Expense), rows)


def _p95(samples: list[float]) -> float:
    return statistics.quantiles(samples, n=20)[-1]


@pytest.mark.usefixtures("patched_jwks")
async def test_summary_and_list_at_five_thousand_expenses_meet_nfr_3(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    await _seed(session_factory=session_factory, user_id=user_id)
    headers = auth_headers(signing_key, settings, user_id=user_id)
    periods = (await graphql(client, headers, PERIODS))["expensePeriods"]
    this_year = next(period for period in periods if period["key"] == "THIS_YEAR")
    variables = {"filter": {"start": this_year["start"], "end": this_year["end"]}}

    timings: dict[str, list[float]] = {"summary": [], "list": []}
    for _ in range(RUNS):
        for name, query in (("summary", SUMMARY), ("list", LIST)):
            started = time.perf_counter()
            await graphql(client, headers, query, variables)
            timings[name].append(time.perf_counter() - started)

    for name, samples in timings.items():
        print(
            f"NFR-3 {name}: p50 {statistics.median(samples):.3f}s, "
            f"p95 {_p95(samples):.3f}s over {RUNS} calls"
        )
    assert _p95(timings["summary"]) < TARGET_P95_SECONDS
    assert _p95(timings["list"]) < TARGET_P95_SECONDS
