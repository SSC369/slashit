"""Epic 006, sub-plan 4.2: summaries end to end against a real database, under
Row Level Security. C-27 to C-30. No model is called on any of these paths."""

import uuid
from datetime import date
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from app.domains.expenses.interfaces.dtos import ExpenseCategory
from app.domains.expenses.repositories.expense_repository import SqlExpenseRepository
from tests.integration.expense_harness import (
    auth_headers,
    graphql,
    patched_jwks,
    seed_expense,
    signing_key,
)

__all__ = ["patched_jwks", "signing_key"]

PERIODS = "query { expensePeriods { key label phrase start end } }"

SUMMARY_FIELDS = (
    "label phrase start end count grandTotalPaise totals { category totalPaise }"
)

SUMMARY = f"""
query($filter: ExpensesFilterInput) {{
  expenseSummary(filter: $filter) {{ {SUMMARY_FIELDS} }}
}}
"""

SUBMIT_SUMMARY = f"""
mutation($rawInput: String!) {{
  submitCapture(rawInput: $rawInput) {{
    __typename
    ... on ExpenseSummary {{ {SUMMARY_FIELDS} }}
    ... on ExpenseRefused {{ message reason }}
  }}
}}
"""


async def _period(
    client: AsyncClient, headers: dict[str, str], *, key: str
) -> dict[str, Any]:
    periods: list[dict[str, Any]] = (await graphql(client, headers, PERIODS))[
        "expensePeriods"
    ]
    return next(period for period in periods if period["key"] == key)


@pytest.mark.usefixtures("patched_jwks")
async def test_totals_are_exact_to_the_paisa_as_paise_strings(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-27, NFR-6."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    this_month = await _period(client, headers, key="THIS_MONTH")
    first = date.fromisoformat(this_month["start"])
    for paise in (1, 99_99_99_999_99, 85_050):
        await seed_expense(
            session_factory=session_factory,
            user_id=user_a,
            amount_paise=paise,
            category=ExpenseCategory.FOOD,
            spent_on=first,
        )

    summary = (
        await graphql(
            client,
            headers,
            SUMMARY,
            {"filter": {"start": this_month["start"], "end": this_month["end"]}},
        )
    )["expenseSummary"]

    assert summary["grandTotalPaise"] == str(1 + 99_99_99_999_99 + 85_050)
    assert summary["totals"] == [
        {"category": "FOOD", "totalPaise": str(1 + 99_99_99_999_99 + 85_050)}
    ]
    assert summary["count"] == 3
    assert summary["label"] == this_month["label"]


@pytest.mark.usefixtures("patched_jwks")
async def test_totals_skip_empty_categories_order_largest_first_and_drop_deleted(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-28, FR-22, FR-25. A tie falls back to FR-9's order: Food before
    Transport."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    this_month = await _period(client, headers, key="THIS_MONTH")
    first = date.fromisoformat(this_month["start"])
    for paise, category in [
        (500, ExpenseCategory.TRANSPORT),
        (500, ExpenseCategory.FOOD),
        (9_000, ExpenseCategory.BILLS),
    ]:
        await seed_expense(
            session_factory=session_factory,
            user_id=user_a,
            amount_paise=paise,
            category=category,
            spent_on=first,
        )
    deleted = await seed_expense(
        session_factory=session_factory,
        user_id=user_a,
        amount_paise=50_000,
        category=ExpenseCategory.HEALTH,
        spent_on=first,
    )
    async with session_factory() as session:
        await SqlExpenseRepository(session).soft_delete(
            user_id=user_a, expense_id=deleted.id
        )

    summary = (
        await graphql(
            client,
            headers,
            SUMMARY,
            {"filter": {"start": this_month["start"], "end": this_month["end"]}},
        )
    )["expenseSummary"]

    assert [total["category"] for total in summary["totals"]] == [
        "BILLS",
        "FOOD",
        "TRANSPORT",
    ]
    assert summary["grandTotalPaise"] == "10000"


@pytest.mark.usefixtures("patched_jwks")
async def test_the_command_and_the_band_give_the_same_totals(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-29, FR-28: `/expenses last month` and the picker's Last month."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    last_month = await _period(client, headers, key="LAST_MONTH")
    for spent_on, paise in [
        (last_month["start"], 1_200),
        (last_month["end"], 3_400),
    ]:
        await seed_expense(
            session_factory=session_factory,
            user_id=user_a,
            amount_paise=paise,
            spent_on=date.fromisoformat(spent_on),
        )

    typed = (
        await graphql(
            client, headers, SUBMIT_SUMMARY, {"rawInput": "/expenses last month"}
        )
    )["submitCapture"]
    picked = (
        await graphql(
            client,
            headers,
            SUMMARY,
            {"filter": {"start": last_month["start"], "end": last_month["end"]}},
        )
    )["expenseSummary"]

    assert typed.pop("__typename") == "ExpenseSummary"
    assert typed == picked
    assert picked["grandTotalPaise"] == "4600"
    assert picked["label"] == last_month["label"]


@pytest.mark.usefixtures("patched_jwks")
async def test_a_period_off_the_list_is_refused_with_the_text_quoted(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-27."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)

    refused = (
        await graphql(
            client, headers, SUBMIT_SUMMARY, {"rawInput": "/expenses since diwali"}
        )
    )["submitCapture"]

    assert refused["__typename"] == "ExpenseRefused"
    assert refused["reason"] == "PERIOD_NOT_UNDERSTOOD"
    assert "“since diwali”" in refused["message"]


@pytest.mark.usefixtures("patched_jwks")
async def test_user_b_never_counts_user_a_expenses(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-30, NFR-1, T7: the band, the command and All time, as user B. The
    sum under RLS alone is slice 1's boundary test."""
    user_a, user_b = two_users
    as_b = auth_headers(signing_key, settings, user_id=user_b)
    this_month = await _period(client, as_b, key="THIS_MONTH")
    await seed_expense(
        session_factory=session_factory,
        user_id=user_a,
        amount_paise=777,
        spent_on=date.fromisoformat(this_month["start"]),
    )

    band = (
        await graphql(
            client,
            as_b,
            SUMMARY,
            {"filter": {"start": this_month["start"], "end": this_month["end"]}},
        )
    )["expenseSummary"]
    all_time = (await graphql(client, as_b, SUMMARY))["expenseSummary"]
    typed = (await graphql(client, as_b, SUBMIT_SUMMARY, {"rawInput": "/expenses"}))[
        "submitCapture"
    ]

    for summary in (band, all_time, typed):
        assert (summary["count"], summary["grandTotalPaise"], summary["totals"]) == (
            0,
            "0",
            [],
        )
    assert all_time["label"] == "All time"
