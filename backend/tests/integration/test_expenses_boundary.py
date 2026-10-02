"""Epic 006, sub-plan 4.1, C-17: rule T7 for expenses. User B asks for user
A's expense by every path, by its exact id, and gets nothing, through the whole
stack under Row Level Security (NFR-1)."""

import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core.db import user_transaction
from app.core.settings import Settings
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


@pytest.mark.usefixtures("patched_jwks")
async def test_user_b_never_reads_edits_or_deletes_user_a_expense(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_a, user_b = two_users
    expense = await seed_expense(session_factory=session_factory, user_id=user_a)
    as_b = auth_headers(signing_key, settings, user_id=user_b)
    expense_id = str(expense.id)

    assert (await graphql(client, as_b, EXPENSES))["expenses"] == []
    assert expense_id not in {
        row.get("id") for row in (await graphql(client, as_b, RECORDS))["records"]
    }
    detail = (await graphql(client, as_b, EXPENSE, {"id": expense_id}))["expense"]
    assert detail["__typename"] == "ExpenseNotFound"
    edit = (
        await graphql(
            client,
            as_b,
            UPDATE,
            {"id": expense_id, "input": {"amountPaise": "1", "description": "x"}},
        )
    )["updateExpense"]
    assert edit["__typename"] == "ExpenseNotFound"
    deleted = (await graphql(client, as_b, DELETE, {"id": expense_id}))["deleteExpense"]
    assert deleted["__typename"] == "ExpenseNotFound"

    as_a = auth_headers(signing_key, settings, user_id=user_a)
    untouched = (await graphql(client, as_a, EXPENSE, {"id": expense_id}))["expense"]
    assert untouched["amountPaise"] == "85000"
    assert untouched["description"] == "dinner with friends"


async def test_rls_alone_hides_the_row_from_another_user(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """The second lock: a query with no user filter still sees only its own
    rows, and a sum can only add the caller's paise (build plan §6)."""
    user_a, user_b = two_users
    await seed_expense(session_factory=session_factory, user_id=user_a)

    async with (
        session_factory() as session,
        user_transaction(session, user_b) as scoped,
    ):
        seen = await scoped.scalar(text("SELECT count(*) FROM expenses"))
        total = await scoped.scalar(
            text("SELECT coalesce(sum(amount_paise), 0) FROM expenses")
        )
    assert seen == 0
    assert total == 0
