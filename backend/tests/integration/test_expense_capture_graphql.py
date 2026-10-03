"""Epic 006, sub-plan 4.1, T-1.7: `/add-expense` end to end against a real
database. The union members, the four questions with their drafts stored in
``pending_captures``, the turns, and the events, with only the model faked."""

import uuid
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core.settings import Settings
from app.domains.gateway.errors import ProviderUnavailableError
from app.domains.gateway.interfaces.dtos import ExtractionRequest, ProviderResult
from app.domains.gateway.services.langchain_provider import LangChainGeminiProvider
from tests.integration.expense_harness import (
    ANSWER,
    SUBMIT,
    auth_headers,
    graphql,
    patched_jwks,
    scripted_model,
    signing_key,
)

__all__ = ["patched_jwks", "scripted_model", "signing_key"]

HISTORY = "query { captureHistory { items { outcome resultingExpenseId } } }"


async def _submit(
    client: AsyncClient, headers: dict[str, str], raw_input: str
) -> dict[str, Any]:
    result: dict[str, Any] = (
        await graphql(client, headers, SUBMIT, {"rawInput": raw_input})
    )["submitCapture"]
    return result


async def _answer(
    client: AsyncClient, headers: dict[str, str], pending_id: str, answer: str
) -> dict[str, Any]:
    result: dict[str, Any] = (
        await graphql(client, headers, ANSWER, {"id": pending_id, "answer": answer})
    )["answerPendingCapture"]
    return result


async def _count_events(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    user_id: uuid.UUID,
    event_type: str,
) -> int:
    async with session_factory() as session:
        count = await session.scalar(
            text(
                "SELECT count(*) FROM events WHERE user_id = :user_id "
                "AND event_type = :event_type"
            ),
            {"user_id": user_id, "event_type": event_type},
        )
    return int(count or 0)


@pytest.mark.usefixtures("patched_jwks")
async def test_a_whole_line_saves_and_its_turn_points_at_the_expense(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
    scripted_model: dict[str, dict[str, Any]],
) -> None:
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    scripted_model["₹850 dinner with friends yesterday"] = {
        "amounts": ["₹850"],
        "description": "dinner with friends",
        "category": "food",
        "local_date": "2026-01-01",
        "date_words": "yesterday",
    }

    saved = await _submit(
        client, headers, "/add-expense ₹850 dinner with friends yesterday"
    )

    assert saved["__typename"] == "ExpenseSaved"
    expense = saved["expense"]
    assert expense["amountPaise"] == "85000"
    assert expense["description"] == "dinner with friends"
    assert expense["category"] == "FOOD"
    assert expense["spentOn"] == "2026-01-01"
    assert expense["origin"] == "command"
    assert expense["originalInput"] == "/add-expense ₹850 dinner with friends yesterday"
    history = (await graphql(client, headers, HISTORY))["captureHistory"]["items"]
    assert history[0] == {
        "outcome": "EXPENSE_SAVED",
        "resultingExpenseId": expense["id"],
    }
    assert (
        await _count_events(session_factory, user_id=user_a, event_type="expense_saved")
        == 1
    )


@pytest.mark.usefixtures("patched_jwks")
async def test_chained_questions_keep_the_draft_in_the_database(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
    scripted_model: dict[str, dict[str, Any]],
) -> None:
    """C-8 then C-7, chained: the choice, then the description, each stored
    in typed columns between requests (AD-6)."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    scripted_model["2 coffees 180"] = {
        "amounts": ["2", "180"],
        "description": "",
        "category": "other",
    }
    scripted_model["coffee with Arjun"] = {"category": "food"}

    choice = await _submit(client, headers, "/add-expense 2 coffees 180")

    assert choice["__typename"] == "ExpenseQuestionAsked"
    assert choice["kind"] == "AMOUNT_CHOICE"
    assert choice["question"] == "Which number is the amount?"
    assert choice["amountCandidates"] == ["200", "18000"]
    assert choice["readDate"] is None
    assert (
        await _count_events(
            session_factory, user_id=user_a, event_type="expense_amount_asked"
        )
        == 1
    )

    description = await _answer(client, headers, choice["pendingCaptureId"], "18000")

    assert description["kind"] == "DESCRIPTION"
    async with session_factory() as session:
        rows = (
            await session.execute(
                text(
                    "SELECT id, missing_field, expense_amount_paise, "
                    "amount_candidates FROM pending_captures WHERE user_id = :user_id"
                ),
                {"user_id": user_a},
            )
        ).all()
    assert [(str(row[0]), row[1], row[2], row[3]) for row in rows] == [
        (description["pendingCaptureId"], "expense_description", 18_000, None)
    ]

    saved = await _answer(
        client, headers, description["pendingCaptureId"], "coffee with Arjun"
    )

    assert saved["__typename"] == "ExpenseSaved"
    assert saved["expense"]["amountPaise"] == "18000"
    assert saved["expense"]["description"] == "coffee with Arjun"
    assert saved["expense"]["category"] == "FOOD"
    assert saved["expense"]["originalInput"] == "/add-expense 2 coffees 180"


@pytest.mark.usefixtures("patched_jwks")
async def test_a_future_date_waits_for_a_confirmed_date(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    scripted_model: dict[str, dict[str, Any]],
) -> None:
    """C-9, FR-8."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    scripted_model["₹1,200 concert tickets next Saturday"] = {
        "amounts": ["₹1,200"],
        "description": "concert tickets",
        "category": "entertainment",
        "local_date": "2099-10-10",
        "date_words": "next Saturday",
    }

    question = await _submit(
        client, headers, "/add-expense ₹1,200 concert tickets next Saturday"
    )

    assert question["kind"] == "DATE"
    assert question["readDate"] == "2099-10-10"
    assert question["question"].startswith("Next Saturday reads as Sat 10 Oct")

    saved = await _answer(client, headers, question["pendingCaptureId"], "2099-10-03")

    assert saved["expense"]["spentOn"] == "2099-10-03"
    assert saved["expense"]["amountPaise"] == "120000"


@pytest.mark.usefixtures("patched_jwks")
async def test_refusals_save_nothing(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
    scripted_model: dict[str, dict[str, Any]],
) -> None:
    """C-4, C-11, FR-6, FR-13."""
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)
    long_description = ("the long story of the team offsite dinner " * 6).strip()
    scripted_model[f"₹4,500 {long_description}"] = {
        "amounts": ["₹4,500"],
        "description": long_description,
        "category": "food",
    }

    currency = await _submit(client, headers, "/add-expense $20 lunch in Singapore")
    too_long = await _submit(client, headers, f"/add-expense ₹4,500 {long_description}")

    assert currency == {
        "__typename": "ExpenseRefused",
        "message": (
            "Slashit records rupees only for now. Enter the amount in ₹ and it "
            "will save."
        ),
        "reason": "FOREIGN_CURRENCY",
        "length": None,
    }
    assert too_long["reason"] == "DESCRIPTION_TOO_LONG"
    assert too_long["length"] == len(long_description)
    assert too_long["message"].endswith("It can be up to 200.")
    async with session_factory() as session:
        stored = await session.scalar(
            text("SELECT count(*) FROM expenses WHERE user_id = :user_id"),
            {"user_id": user_a},
        )
    assert stored == 0
    assert (
        await _count_events(
            session_factory, user_id=user_a, event_type="expense_currency_refused"
        )
        == 1
    )


@pytest.mark.usefixtures("patched_jwks")
async def test_a_model_outage_is_the_gateways_own_refusal(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C-12, FR-14."""

    async def generate(
        self: LangChainGeminiProvider, request: ExtractionRequest
    ) -> ProviderResult:
        raise ProviderUnavailableError()

    monkeypatch.setattr(LangChainGeminiProvider, "generate", generate)
    user_a, _ = two_users
    headers = auth_headers(signing_key, settings, user_id=user_a)

    outcome = await _submit(client, headers, "/add-expense ₹640 pharmacy")

    assert outcome["__typename"] == "ProviderUnavailable"


@pytest.mark.usefixtures("patched_jwks")
async def test_user_b_cannot_answer_user_a_expense_question(
    client: AsyncClient,
    settings: Settings,
    signing_key: ec.EllipticCurvePrivateKey,
    two_users: tuple[uuid.UUID, uuid.UUID],
    scripted_model: dict[str, dict[str, Any]],
) -> None:
    """NFR-1: a pending draft holds an amount; it is A's alone."""
    user_a, user_b = two_users
    question = await _submit(
        client, auth_headers(signing_key, settings, user_id=user_a), "/add-expense"
    )

    response = await client.post(
        "/graphql",
        json={
            "query": ANSWER,
            "variables": {"id": question["pendingCaptureId"], "answer": "850"},
        },
        headers=auth_headers(signing_key, settings, user_id=user_b),
    )

    assert response.json()["data"] is None
