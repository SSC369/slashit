"""Epic 006, sub-plan 4.1: Records' expense queries and mutations end to end
against a real database. C-14, C-15, C-16, C-19, C-20, and the table's own
checks."""

import uuid
from datetime import date

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core.db import user_transaction
from app.core.settings import Settings
from app.domains.expenses.interfaces.dtos import ExpenseCategory
from tests.integration.expense_harness import (
    DELETE,
    EXPENSE,
    EXPENSES,
    RECORDS,
    UPDATE,
    auth_headers,
    graphql,
    patched_jwks,
    seed_expense,
    signing_key,
)

__all__ = ["patched_jwks", "signing_key"]

FIVE_CRORE_PAISE = 5_000_000_000


@pytest.mark.usefixtures("patched_jwks")
async def test_the_list_filters_by_category_and_range_newest_first(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-14, FR-16, FR-17."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    older = await seed_expense(
        session_factory=session_factory, user_id=user_a, spent_on=date(2026, 9, 28)
    )
    newer = await seed_expense(
        session_factory=session_factory, user_id=user_a, spent_on=date(2026, 10, 1)
    )
    cab = await seed_expense(
        session_factory=session_factory,
        user_id=user_a,
        description="cab",
        category=ExpenseCategory.TRANSPORT,
        spent_on=date(2026, 10, 2),
    )

    every = (await graphql(client, headers, EXPENSES))["expenses"]
    food = (await graphql(client, headers, EXPENSES, {"filter": {"category": "FOOD"}}))[
        "expenses"
    ]
    october = (
        await graphql(
            client,
            headers,
            EXPENSES,
            {"filter": {"start": "2026-10-01", "end": "2026-10-31"}},
        )
    )["expenses"]

    assert [row["id"] for row in every] == [str(cab.id), str(newer.id), str(older.id)]
    assert [row["id"] for row in food] == [str(newer.id), str(older.id)]
    assert [row["id"] for row in october] == [str(cab.id), str(newer.id)]
    assert every[1]["spentOn"] == "2026-10-01"
    assert every[1]["category"] == "FOOD"


@pytest.mark.usefixtures("patched_jwks")
async def test_five_crore_round_trips_as_paise(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-19, FR-2: past GraphQL Int's 32 bits, unchanged both ways."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    expense = await seed_expense(
        session_factory=session_factory, user_id=user_a, amount_paise=FIVE_CRORE_PAISE
    )

    detail = (await graphql(client, headers, EXPENSE, {"id": str(expense.id)}))[
        "expense"
    ]
    assert detail["amountPaise"] == "5000000000"

    updated = (
        await graphql(
            client,
            headers,
            UPDATE,
            {"id": str(expense.id), "input": {"amountPaise": "5000000001"}},
        )
    )["updateExpense"]
    assert updated["amountPaise"] == "5000000001"


@pytest.mark.usefixtures("patched_jwks")
async def test_each_field_edits_and_invalid_edits_are_refused(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-15, FR-21."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    expense = await seed_expense(session_factory=session_factory, user_id=user_a)

    async def edit(changes: dict[str, object]) -> dict[str, object]:
        data = await graphql(
            client, headers, UPDATE, {"id": str(expense.id), "input": changes}
        )
        result: dict[str, object] = data["updateExpense"]
        return result

    renamed = await edit({"description": "team dinner"})
    assert renamed["description"] == "team dinner"
    assert renamed["category"] == "FOOD"
    assert renamed["updatedAt"] != renamed["createdAt"]

    assert (await edit({"category": "ENTERTAINMENT"}))["category"] == "ENTERTAINMENT"
    assert (await edit({"spentOn": "2027-01-15"}))["spentOn"] == "2027-01-15"
    assert (await edit({"amountPaise": "90000"}))["amountPaise"] == "90000"

    zero = await edit({"amountPaise": "0"})
    assert zero == {
        "__typename": "ExpenseInvalid",
        "message": "Enter an amount above ₹0.",
        "field": "AMOUNT",
        "reason": "NOT_POSITIVE",
        "length": None,
    }
    too_long = await edit({"description": "d" * 201})
    assert too_long["reason"] == "TOO_LONG"
    assert too_long["length"] == 201


@pytest.mark.usefixtures("patched_jwks")
async def test_delete_leaves_every_view_and_a_second_delete_is_not_found(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-16, C-20, FR-19, FR-22."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    expense = await seed_expense(session_factory=session_factory, user_id=user_a)

    all_tab = (await graphql(client, headers, RECORDS))["records"]
    assert {
        "__typename": "Expense",
        "id": str(expense.id),
        "amountPaise": "85000",
    } in all_tab

    deleted = (await graphql(client, headers, DELETE, {"id": str(expense.id)}))[
        "deleteExpense"
    ]
    assert deleted == {"__typename": "ExpenseDeleted", "id": str(expense.id)}

    assert (await graphql(client, headers, EXPENSES))["expenses"] == []
    detail = (await graphql(client, headers, EXPENSE, {"id": str(expense.id)}))[
        "expense"
    ]
    assert detail["__typename"] == "ExpenseNotFound"
    all_tab = (await graphql(client, headers, RECORDS))["records"]
    assert str(expense.id) not in {row.get("id") for row in all_tab}
    again = (await graphql(client, headers, DELETE, {"id": str(expense.id)}))[
        "deleteExpense"
    ]
    assert again["__typename"] == "ExpenseNotFound"
    edit = (
        await graphql(
            client,
            headers,
            UPDATE,
            {"id": str(expense.id), "input": {"description": "x"}},
        )
    )["updateExpense"]
    assert edit["__typename"] == "ExpenseNotFound"

    async with session_factory() as session:
        stamped = await session.scalar(
            text("SELECT deleted_at IS NOT NULL FROM expenses WHERE id = :id"),
            {"id": expense.id},
        )
    assert stamped is True


@pytest.mark.parametrize(
    ("amount_paise", "description"),
    [(0, "tea"), (-100, "tea"), (100, ""), (100, "d" * 201)],
)
async def test_the_table_refuses_what_the_rules_refuse(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
    amount_paise: int,
    description: str,
) -> None:
    """Build plan §3: both checks hold in the database, not only in code."""
    user_a, _ = two_users
    async with session_factory() as session:
        with pytest.raises(IntegrityError):
            async with user_transaction(session, user_a) as scoped:
                await scoped.execute(
                    text(
                        "INSERT INTO expenses (id, user_id, amount_paise, description,"
                        " category, spent_on, origin, original_input, created_at,"
                        " updated_at) VALUES (gen_random_uuid(), :user_id, :amount,"
                        " :description, 'food', '2026-10-01', 'command', 'x', now(),"
                        " now())"
                    ),
                    {
                        "user_id": user_a,
                        "amount": amount_paise,
                        "description": description,
                    },
                )


async def test_search_vector_holds_the_description_and_the_category(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """FR-29's columns ship now: "food" finds a dinner by its category."""
    user_a, _ = two_users
    expense = await seed_expense(session_factory=session_factory, user_id=user_a)

    async with (
        session_factory() as session,
        user_transaction(session, user_a) as scoped,
    ):
        matched = await scoped.scalar(
            text(
                "SELECT count(*) FROM expenses WHERE id = :id AND search_vector"
                " @@ to_tsquery('english', 'food & friends')"
            ),
            {"id": expense.id},
        )
    assert matched == 1
