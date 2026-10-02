"""Epic 006 edge cases, end to end against a real database with only the model
faked: malformed ids, amounts at and past the storage limit, text the client
must render as text, period boundaries, and actions on deleted expenses."""

import uuid
from datetime import date, timedelta
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from app.domains.expenses.repositories.expense_repository import SqlExpenseRepository
from tests.integration.expense_harness import (
    DELETE,
    EXPENSE,
    EXPENSES,
    SUBMIT,
    UPDATE,
    auth_headers,
    graphql,
    patched_jwks,
    scripted_model,
    seed_expense,
    signing_key,
)

__all__ = ["patched_jwks", "scripted_model", "signing_key"]

PERIODS = "query { expensePeriods { key start end } }"
SUMMARY = """
query($filter: ExpensesFilterInput) {
  expenseSummary(filter: $filter) { count grandTotalPaise totals { category totalPaise } }
}
"""
SUMMARISE = """
mutation($rawInput: String!) {
  submitCapture(rawInput: $rawInput) {
    __typename
    ... on ExpenseSummary { label count grandTotalPaise }
    ... on ExpenseRefused { reason }
  }
}
"""


async def _raw(
    client: AsyncClient,
    headers: dict[str, str],
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The whole response body, errors included."""
    response = await client.post(
        "/graphql", json={"query": query, "variables": variables or {}}, headers=headers
    )
    body: dict[str, Any] = response.json()
    return body


def _amount_line(*, scripts: dict[str, dict[str, Any]], text: str, amount: str) -> None:
    scripts[text] = {"amounts": [amount], "description": "gold", "category": "shopping"}


@pytest.mark.usefixtures("patched_jwks")
@pytest.mark.parametrize("bad_id", ["abc", "123", "", "not-a-uuid-at-all"])
async def test_a_malformed_id_reads_as_not_found(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    bad_id: str,
) -> None:
    """A hand-typed URL such as /records/expenses/abc is a missing expense,
    not a server error."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)

    detail = await _raw(client, headers, EXPENSE, {"id": bad_id})
    edit = await _raw(
        client, headers, UPDATE, {"id": bad_id, "input": {"description": "x"}}
    )
    deleted = await _raw(client, headers, DELETE, {"id": bad_id})

    assert detail.get("errors") is None, detail
    assert detail["data"]["expense"]["__typename"] == "ExpenseNotFound"
    assert edit["data"]["updateExpense"]["__typename"] == "ExpenseNotFound"
    assert deleted["data"]["deleteExpense"]["__typename"] == "ExpenseNotFound"


@pytest.mark.usefixtures("patched_jwks")
async def test_an_amount_past_two_to_the_53_saves_and_sums_exactly(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    scripted_model: dict[str, dict[str, Any]],
) -> None:
    """FR-2 and NFR-6: ₹10,00,00,00,00,00,000 is 10^14 rupees, 10^16 paise,
    past a float's exact range (2^53), and still exact through GraphQL and the
    sum."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    text = "₹10,00,00,00,00,00,000 gold"
    _amount_line(scripts=scripted_model, text=text, amount="₹10,00,00,00,00,00,000")

    saved = (
        await graphql(client, headers, SUBMIT, {"rawInput": f"/add-expense {text}"})
    )["submitCapture"]
    twice = (
        await graphql(client, headers, SUBMIT, {"rawInput": f"/add-expense {text}"})
    )["submitCapture"]
    summary = (await graphql(client, headers, SUMMARY))["expenseSummary"]

    assert saved["__typename"] == "ExpenseSaved", saved
    assert twice["__typename"] == "ExpenseSaved", twice
    assert saved["expense"]["amountPaise"] == str(10**16)
    assert summary["grandTotalPaise"] == str(2 * 10**16)


@pytest.mark.usefixtures("patched_jwks")
async def test_an_amount_past_the_storage_limit_is_refused_not_a_server_error(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    scripted_model: dict[str, dict[str, Any]],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """A bigint holds about 9.2 × 10^18 paise. A typo past it must not reach
    the database as an overflow."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    huge = "1" + "0" * 20
    text = f"{huge} gold"
    _amount_line(scripts=scripted_model, text=text, amount=huge)

    body = await _raw(client, headers, SUBMIT, {"rawInput": f"/add-expense {text}"})
    expense = await seed_expense(session_factory=session_factory, user_id=user_a)
    edit = await _raw(
        client,
        headers,
        UPDATE,
        {"id": str(expense.id), "input": {"amountPaise": "9" * 25}},
    )

    assert body.get("errors") is None, body
    assert body["data"]["submitCapture"]["__typename"] != "ExpenseSaved"
    assert edit.get("errors") is None, edit
    assert edit["data"]["updateExpense"]["__typename"] == "ExpenseInvalid"


@pytest.mark.usefixtures("patched_jwks")
async def test_a_long_expense_line_is_refused_as_a_long_description(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    scripted_model: dict[str, dict[str, Any]],
) -> None:
    """FR-13 with the text kept: a line past 001's 500-character cap is still
    answered with the typed refusal, never a raw server error."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    description = "team offsite dinner " * 30
    text = f"₹4,500 {description}".strip()
    scripted_model[text] = {
        "amounts": ["₹4,500"],
        "description": description.strip(),
        "category": "food",
    }

    body = await _raw(client, headers, SUBMIT, {"rawInput": f"/add-expense {text}"})

    assert body.get("errors") is None, body
    refused = body["data"]["submitCapture"]
    assert refused["__typename"] == "ExpenseRefused"
    assert refused["reason"] == "DESCRIPTION_TOO_LONG"


@pytest.mark.usefixtures("patched_jwks")
async def test_markup_and_emoji_are_stored_and_returned_as_typed(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    text = "<script>alert(1)</script> chai ☕️ & samosa"
    expense = await seed_expense(
        session_factory=session_factory, user_id=user_a, description=text
    )

    detail = (await graphql(client, headers, EXPENSE, {"id": str(expense.id)}))[
        "expense"
    ]

    assert detail["description"] == text


@pytest.mark.usefixtures("patched_jwks")
async def test_a_description_is_measured_in_characters_not_bytes(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """FR-13's 200 is characters. 200 emoji pass the table's check and the
    service; 201 are refused."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    expense = await seed_expense(session_factory=session_factory, user_id=user_a)

    fits = (
        await graphql(
            client,
            headers,
            UPDATE,
            {"id": str(expense.id), "input": {"description": "😀" * 200}},
        )
    )["updateExpense"]
    over = (
        await graphql(
            client,
            headers,
            UPDATE,
            {"id": str(expense.id), "input": {"description": "😀" * 201}},
        )
    )["updateExpense"]
    blank = (
        await graphql(
            client,
            headers,
            UPDATE,
            {"id": str(expense.id), "input": {"description": "   "}},
        )
    )["updateExpense"]

    assert fits["__typename"] == "Expense"
    assert (over["__typename"], over["reason"], over["length"]) == (
        "ExpenseInvalid",
        "TOO_LONG",
        201,
    )
    assert (blank["__typename"], blank["reason"]) == ("ExpenseInvalid", "EMPTY")


@pytest.mark.usefixtures("patched_jwks")
@pytest.mark.parametrize(
    ("amount", "reason"), [("0", "NOT_POSITIVE"), ("-500", "NOT_POSITIVE")]
)
async def test_an_edit_to_zero_or_below_is_invalid(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
    amount: str,
    reason: str,
) -> None:
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    expense = await seed_expense(session_factory=session_factory, user_id=user_a)

    edit = (
        await graphql(
            client,
            headers,
            UPDATE,
            {"id": str(expense.id), "input": {"amountPaise": amount}},
        )
    )["updateExpense"]

    assert (edit["__typename"], edit["field"], edit["reason"]) == (
        "ExpenseInvalid",
        "AMOUNT",
        reason,
    )


@pytest.mark.usefixtures("patched_jwks")
async def test_period_edges_are_inclusive_and_a_future_day_this_month_counts(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """The first and last days of last month count in it; the day before and
    the day after do not. The last day of this month, still ahead, counts in
    this month (PRD assumption under FR-22)."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    periods = {
        period["key"]: period
        for period in (await graphql(client, headers, PERIODS))["expensePeriods"]
    }
    last_start = date.fromisoformat(periods["LAST_MONTH"]["start"])
    last_end = date.fromisoformat(periods["LAST_MONTH"]["end"])
    this_end = date.fromisoformat(periods["THIS_MONTH"]["end"])
    for spent_on, paise in [
        (last_start - timedelta(days=1), 1),
        (last_start, 10),
        (last_end, 100),
        (last_end + timedelta(days=1), 1_000),
        (this_end, 10_000),
    ]:
        await seed_expense(
            session_factory=session_factory,
            user_id=user_a,
            amount_paise=paise,
            spent_on=spent_on,
        )

    last = (
        await graphql(client, headers, SUMMARISE, {"rawInput": "/expenses last month"})
    )["submitCapture"]
    this = (await graphql(client, headers, SUMMARISE, {"rawInput": "/expenses"}))[
        "submitCapture"
    ]

    assert (last["count"], last["grandTotalPaise"]) == (2, "110")
    assert (this["count"], this["grandTotalPaise"]) == (2, "11000")


@pytest.mark.usefixtures("patched_jwks")
@pytest.mark.parametrize(
    "raw_input",
    ["/expenses   LAST   Month  ", "/expenses Last month", "/EXPENSES last month"],
)
async def test_the_command_reads_case_and_spacing_loosely(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    raw_input: str,
) -> None:
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)

    body = await _raw(client, headers, SUMMARISE, {"rawInput": raw_input})

    assert body.get("errors") is None, body
    assert body["data"]["submitCapture"]["__typename"] in {
        "ExpenseSummary",
        # A command name is matched exactly, as every other command is.
        "UnrecognisedCommand",
    }
    if raw_input.startswith("/expenses"):
        assert body["data"]["submitCapture"]["__typename"] == "ExpenseSummary"


@pytest.mark.usefixtures("patched_jwks")
async def test_a_deleted_expense_cannot_be_edited_deleted_or_counted(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    expense = await seed_expense(session_factory=session_factory, user_id=user_a)
    async with session_factory() as session:
        await SqlExpenseRepository(session).soft_delete(
            user_id=user_a, expense_id=expense.id
        )

    edit = (
        await graphql(
            client,
            headers,
            UPDATE,
            {"id": str(expense.id), "input": {"description": "x"}},
        )
    )["updateExpense"]
    again = (await graphql(client, headers, DELETE, {"id": str(expense.id)}))[
        "deleteExpense"
    ]
    listed = (await graphql(client, headers, EXPENSES))["expenses"]
    summary = (await graphql(client, headers, SUMMARY))["expenseSummary"]

    assert edit["__typename"] == "ExpenseNotFound"
    assert again["__typename"] == "ExpenseNotFound"
    assert listed == []
    assert summary["count"] == 0
