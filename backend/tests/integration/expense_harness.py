"""Shared harness for epic 006's expense tests: auth, a scripted model,
GraphQL helpers and a seeded expense.

The model is the one thing faked: ``LangChainGeminiProvider.generate`` is
patched at the class, so the gateway, capture, expenses and the database all
run for real, under Row Level Security.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import auth as auth_module
from app.core.settings import Settings
from app.domains.expenses.interfaces.dtos import ExpenseCategory, ExpenseDTO
from app.domains.expenses.interfaces.repositories import ExpenseWrite
from app.domains.expenses.repositories.expense_repository import SqlExpenseRepository
from app.domains.gateway.interfaces.dtos import ExtractionRequest, ProviderResult
from app.domains.gateway.services.langchain_provider import LangChainGeminiProvider

ALGORITHM = "ES256"

EXPENSE_FIELDS = """
  id amountPaise description category spentOn origin originalInput
  createdAt updatedAt
"""

SUBMIT = f"""
mutation($rawInput: String!) {{
  submitCapture(rawInput: $rawInput) {{
    __typename
    ... on ExpenseSaved {{ expense {{ {EXPENSE_FIELDS} }} }}
    ... on ExpenseQuestionAsked {{
      pendingCaptureId kind question amountCandidates readDate
    }}
    ... on ExpenseRefused {{ message reason length }}
    ... on ProviderUnavailable {{ message }}
  }}
}}
"""

ANSWER = f"""
mutation($id: ID!, $answer: String!) {{
  answerPendingCapture(pendingCaptureId: $id, answer: $answer) {{
    __typename
    ... on ExpenseSaved {{ expense {{ {EXPENSE_FIELDS} }} }}
    ... on ExpenseQuestionAsked {{
      pendingCaptureId kind question amountCandidates readDate
    }}
    ... on ExpenseRefused {{ message reason length }}
  }}
}}
"""

EXPENSES = f"""
query($filter: ExpensesFilterInput) {{
  expenses(filter: $filter) {{ {EXPENSE_FIELDS} }}
}}
"""

EXPENSE = f"""
query($id: ID!) {{
  expense(id: $id) {{
    __typename
    ... on Expense {{ {EXPENSE_FIELDS} }}
    ... on ExpenseNotFound {{ message }}
  }}
}}
"""

UPDATE = f"""
mutation($id: ID!, $input: UpdateExpenseInput!) {{
  updateExpense(id: $id, input: $input) {{
    __typename
    ... on Expense {{ {EXPENSE_FIELDS} }}
    ... on ExpenseNotFound {{ message }}
    ... on ExpenseInvalid {{ message field reason length }}
  }}
}}
"""

DELETE = """
mutation($id: ID!) {
  deleteExpense(id: $id) {
    __typename
    ... on ExpenseDeleted { id }
    ... on ExpenseNotFound { message }
  }
}
"""

RECORDS = """
query {
  records(filter: { kind: "ALL" }) {
    __typename
    ... on Expense { id amountPaise }
    ... on Task { id }
  }
}
"""


@pytest.fixture
def signing_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture
def patched_jwks(
    monkeypatch: pytest.MonkeyPatch, signing_key: ec.EllipticCurvePrivateKey
) -> None:
    class FakeKey:
        key = signing_key.public_key()

    class FakeClient:
        def get_signing_key_from_jwt(self, _token: str) -> FakeKey:
            return FakeKey()

    monkeypatch.setattr(auth_module, "_get_jwks_client", lambda _s: FakeClient())


@pytest.fixture
def scripted_model(monkeypatch: pytest.MonkeyPatch) -> dict[str, dict[str, Any]]:
    """What the model returns for each prompt, set by the test. A prompt with
    no script reads as a food spend with no amount; a category-only call
    reads as food."""
    scripts: dict[str, dict[str, Any]] = {}

    async def generate(
        self: LangChainGeminiProvider, request: ExtractionRequest
    ) -> ProviderResult:
        if request.prompt in scripts:
            data = scripts[request.prompt]
        elif "amounts" in request.schema["properties"]:
            data = {"amounts": [], "description": request.prompt, "category": "food"}
        else:
            data = {"category": "food"}
        return ProviderResult(
            data=data, input_tokens=400, output_tokens=50, model="fake-flash"
        )

    monkeypatch.setattr(LangChainGeminiProvider, "generate", generate)
    return scripts


def auth_headers(
    key: ec.EllipticCurvePrivateKey, settings: Settings, *, user_id: uuid.UUID
) -> dict[str, str]:
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return {"Authorization": f"Bearer {jwt.encode(claims, key, algorithm=ALGORITHM)}"}


async def graphql(
    client: AsyncClient,
    headers: dict[str, str],
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = await client.post(
        "/graphql", json={"query": query, "variables": variables or {}}, headers=headers
    )
    body: dict[str, Any] = response.json()
    assert "errors" not in body, body
    data: dict[str, Any] = body["data"]
    return data


async def seed_expense(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    user_id: uuid.UUID,
    amount_paise: int = 85_000,
    description: str = "dinner with friends",
    category: ExpenseCategory = ExpenseCategory.FOOD,
    spent_on: date = date(2026, 10, 1),
) -> ExpenseDTO:
    async with session_factory() as session:
        return await SqlExpenseRepository(session).create_expense(
            user_id=user_id,
            write=ExpenseWrite(
                amount_paise=amount_paise,
                description=description,
                category=category,
                spent_on=spent_on,
                origin="command",
                original_input=f"/add-expense {description}",
            ),
        )
