"""Epic 006, sub-plan 4.3 §7: C-34 to C-36 and C-39, against PostgreSQL with
only the model faked. Expenses found by words, category, exact amount and
meaning; never across users; `/search 850` end to end."""

import uuid
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.settings import Settings
from app.domains.expenses.interfaces.dtos import ExpenseCategory, ExpenseDTO
from app.domains.expenses.repositories.expense_repository import SqlExpenseRepository
from tests.integration.expense_harness import seed_expense
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
      groups {
        recordType
        total
        hits { record { __typename ... on Expense { id amountPaise } } }
      }
    }
  }
}
"""

SEARCH = """
query($text: String!, $recordType: RecordType) {
  search(text: $text, recordType: $recordType, offset: 0, limit: 50) {
    ... on SearchPage { total hits { __typename ... on Expense { id } } }
  }
}
"""

RELATED = """
query($id: ID!) {
  relatedRecords(recordType: EXPENSE, id: $id) {
    __typename
    ... on Expense { id }
  }
}
"""


async def _seed(
    session_factory: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
    *,
    description: str,
    amount_paise: int = 85_000,
    category: ExpenseCategory = ExpenseCategory.FOOD,
    meaning: str | None = None,
) -> ExpenseDTO:
    expense = await seed_expense(
        session_factory=session_factory,
        user_id=user_id,
        amount_paise=amount_paise,
        description=description,
        category=category,
    )
    if meaning is not None:
        async with session_factory() as session:
            await SqlExpenseRepository(session).set_embedding(
                user_id=user_id,
                expense_id=expense.id,
                description=description,
                embedding=embed_text(meaning),
            )
    return expense


async def _expense_hits(
    client: AsyncClient, headers: dict[str, str], line: str
) -> list[str]:
    data = await graphql(client, headers, SUBMIT, {"rawInput": line})
    groups = data["submitCapture"]["groups"]
    return [
        hit["record"]["id"]
        for group in groups
        if group["recordType"] == "EXPENSE"
        for hit in group["hits"]
    ]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_words_and_category_find_expenses_and_a_deleted_one_never(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-34, FR-29: by description, and by the category's own word."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)
    uber = await _seed(
        session_factory,
        user_id,
        description="Uber to office",
        category=ExpenseCategory.TRANSPORT,
    )
    dinner = await _seed(session_factory, user_id, description="dinner at Toit")
    deleted = await _seed(session_factory, user_id, description="Uber home")
    async with session_factory() as session:
        await SqlExpenseRepository(session).soft_delete(
            user_id=user_id, expense_id=deleted.id
        )

    assert await _expense_hits(client, headers, "/search uber") == [str(uber.id)]
    assert await _expense_hits(client, headers, "/search food") == [str(dinner.id)]
    assert await _expense_hits(client, headers, "/search transport") == [str(uber.id)]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_a_search_that_is_a_number_finds_that_exact_amount(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-35, C-39, FR-30 as 4.3 Q1 reads it: `/search 850` finds both ₹850
    spends, never ₹8,500; `₹850.50` finds only ₹850.50; `1,200` reads as ₹1,200."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)
    first = await _seed(session_factory, user_id, description="dinner")
    second = await _seed(session_factory, user_id, description="cab")
    await _seed(session_factory, user_id, description="phone", amount_paise=850_000)
    with_paise = await _seed(
        session_factory, user_id, description="pharmacy", amount_paise=85_050
    )
    shoes = await _seed(
        session_factory, user_id, description="shoes", amount_paise=120_000
    )

    found = await _expense_hits(client, headers, "/search 850")
    assert sorted(found) == sorted([str(first.id), str(second.id)])
    assert await _expense_hits(client, headers, "/search ₹850.50") == [
        str(with_paise.id)
    ]
    assert await _expense_hits(client, headers, "/search 1,200") == [str(shoes.id)]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_an_amount_match_ranks_above_a_meaning_only_match(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-35, 4.3 Q2: the top tier, with every-word matches."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)
    # Near "850" in meaning only: the fake embedder puts unknown words on one
    # axis, so this row is a meaning match for any number searched.
    near = await _seed(
        session_factory, user_id, description="gift", amount_paise=5_000, meaning="850"
    )
    exact = await _seed(session_factory, user_id, description="dinner")

    found = await _expense_hits(client, headers, "/search 850")

    assert found == [str(exact.id), str(near.id)]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_meaning_finds_an_expense_with_no_shared_word_and_lists_related(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """005 FR-5 and FR-25 for expenses: "visa" finds the passport fee by
    meaning, and its detail lists the other passport-axis expense."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)
    fee = await _seed(
        session_factory, user_id, description="passport office fee", meaning="passport"
    )
    photos = await _seed(
        session_factory, user_id, description="photos for passport", meaning="passport"
    )

    found = await _expense_hits(client, headers, "/search visa")
    related = await graphql(client, headers, RELATED, {"id": str(fee.id)})

    assert sorted(found) == sorted([str(fee.id), str(photos.id)])
    assert related["relatedRecords"] == [
        {"__typename": "Expense", "id": str(photos.id)}
    ]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_records_search_filters_to_expenses(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """005 FR-22: the Expenses tab's box sends EXPENSE."""
    user_id, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_id)
    uber = await _seed(session_factory, user_id, description="Uber to office")

    data = await graphql(
        client, headers, SEARCH, {"text": "uber", "recordType": "EXPENSE"}
    )

    page: dict[str, Any] = data["search"]
    assert page["total"] == 1
    assert page["hits"] == [{"__typename": "Expense", "id": str(uber.id)}]


@pytest.mark.usefixtures("patched_jwks", "keyword_embedder")
async def test_another_users_expense_is_never_found_or_related(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """C-36, NFR-1, T7: user B searching user A's words or amount gets nothing."""
    user_a, user_b = two_users
    expense = await _seed(
        session_factory, user_a, description="Uber to office", meaning="passport"
    )
    headers_b = auth_headers(signing_key, settings, user_id=user_b)

    assert await _expense_hits(client, headers_b, "/search uber") == []
    assert await _expense_hits(client, headers_b, "/search 850") == []
    related = await graphql(client, headers_b, RELATED, {"id": str(expense.id)})
    assert related["relatedRecords"] == []
