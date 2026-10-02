"""Shared harness for epic 005's search tests: auth, a keyword embedder over
fixed axes, a slow embedder, GraphQL helpers and a seeded account.

The model is the one thing faked. The embedder places words on fixed axes, so
"career" and "backend" share one and a meaning match is a real vector search.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core import auth as auth_module
from app.core import deps as deps_module
from app.core.settings import Settings
from app.domains.gateway.constants import EmbedPurpose
from app.domains.gateway.errors import ProviderUnavailableError
from app.domains.gateway.interfaces.dtos import (
    ExtractionRequest,
    ProviderEmbedding,
    ProviderResult,
)
from app.domains.gateway.services.langchain_provider import LangChainGeminiProvider
from app.domains.memories.interfaces.repositories import MemoryWrite
from app.domains.memories.repositories.memory_repository import SqlMemoryRepository
from app.domains.records.repositories.task_repository import SqlTaskRepository

ALGORITHM = "ES256"
DIMENSIONS = 768

# Words the fake embedder places on the same axis: one meaning each.
AXES = {"career": 0, "backend": 0, "engineer": 0, "passport": 1, "visa": 1}
UNRELATED_AXIS = 7

SUBMIT = """
mutation($rawInput: String!) {
  submitCapture(rawInput: $rawInput) {
    __typename
    ... on SearchResults {
      query
      meaningUnavailable
      noSupport
      answerUnavailable
      answer { sentences { text citations } }
      groups {
        recordType
        total
        hits {
          citation
          record {
            __typename
            ... on Task { id title }
            ... on Reminder { id description }
            ... on Memory { id text }
          }
        }
      }
    }
    ... on SearchTooLong { length limit }
    ... on PendingQuestionCreated { pendingCaptureId question }
  }
}
"""

ANSWER = """
mutation($id: ID!, $answer: String!) {
  answerPendingCapture(pendingCaptureId: $id, answer: $answer) {
    __typename
    ... on SearchResults { query groups { recordType total } }
  }
}
"""

HISTORY = """
query { captureHistory { items { inputText outcome } } }
"""


def axis_vector(*, axis: int) -> tuple[float, ...]:
    return tuple(1.0 if index == axis else 0.0 for index in range(DIMENSIONS))


def embed_text(text: str) -> tuple[float, ...]:
    for word in text.lower().split():
        if word.strip("?.,!") in AXES:
            return axis_vector(axis=AXES[word.strip("?.,!")])
    return axis_vector(axis=UNRELATED_AXIS)


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
def keyword_embedder(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Embeds by keyword. Returns every text it was asked to embed."""
    embedded: list[str] = []

    async def embed(
        self: LangChainGeminiProvider, *, text: str, purpose: EmbedPurpose
    ) -> ProviderEmbedding:
        embedded.append(text)
        return ProviderEmbedding(vector=embed_text(text), model="fake-embed")

    monkeypatch.setattr(LangChainGeminiProvider, "embed", embed)
    return embedded


@pytest.fixture
def slow_embedder(monkeypatch: pytest.MonkeyPatch) -> None:
    """An embed that never answers inside the search's budget (FR-20)."""

    async def embed(
        self: LangChainGeminiProvider, *, text: str, purpose: EmbedPurpose
    ) -> ProviderEmbedding:
        await asyncio.sleep(1)
        return ProviderEmbedding(vector=embed_text(text), model="fake-embed")

    monkeypatch.setattr(LangChainGeminiProvider, "embed", embed)
    monkeypatch.setattr(deps_module, "SEARCH_EMBED_TIMEOUT_SECONDS", 0.05)


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


async def submit(
    client: AsyncClient, headers: dict[str, str], raw_input: str
) -> dict[str, Any]:
    data = await graphql(client, headers, SUBMIT, {"rawInput": raw_input})
    result: dict[str, Any] = data["submitCapture"]
    return result


async def seed(
    *, session_factory: async_sessionmaker[AsyncSession], user_id: uuid.UUID
) -> dict[str, uuid.UUID]:
    """A passport memory, a passport task, and a backend task found only by
    meaning, each with the vector the keyword embedder would give it."""
    async with session_factory() as session:
        memory = await SqlMemoryRepository(session).create_memory(
            user_id=user_id,
            write=MemoryWrite(
                text="My passport expires in 2030",
                category=None,
                embedding=embed_text("passport"),
                origin="command",
                original_input=None,
            ),
        )
        tasks = SqlTaskRepository(session)
        passport_task = await tasks.create_task(
            user_id=user_id,
            title="Renew passport",
            due_at=None,
            origin="command",
            original_input=None,
        )
        backend_task = await tasks.create_task(
            user_id=user_id,
            title="Build a REST API with Spring Boot",
            due_at=None,
            origin="command",
            original_input=None,
        )
        for task, vector in (
            (passport_task, embed_text("passport")),
            (backend_task, embed_text("backend")),
        ):
            await tasks.set_embedding(
                user_id=user_id, task_id=task.id, title=task.title, embedding=vector
            )
    return {
        "memory": memory.id,
        "passport_task": passport_task.id,
        "backend_task": backend_task.id,
    }


@pytest.fixture
def answering_model(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Answers from record [1] whenever the prompt has records; says nothing
    supports it when a question mentions "blood". Returns every prompt."""
    prompts: list[str] = []

    async def generate(
        self: LangChainGeminiProvider, request: ExtractionRequest
    ) -> ProviderResult:
        prompts.append(request.prompt)
        if "blood" in request.prompt.lower():
            data: dict[str, Any] = {"sentences": [], "supported": False}
        else:
            data = {
                "sentences": [
                    {"text": "Your passport expires in 2030.", "sources": [1]},
                    {"text": "An uncited guess.", "sources": []},
                ],
                "supported": True,
            }
        return ProviderResult(
            data=data, input_tokens=300, output_tokens=40, model="fake-flash"
        )

    monkeypatch.setattr(LangChainGeminiProvider, "generate", generate)
    return prompts


@pytest.fixture
def refusing_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """The provider is down for generation (FR-19)."""

    async def generate(
        self: LangChainGeminiProvider, request: ExtractionRequest
    ) -> ProviderResult:
        raise ProviderUnavailableError()

    monkeypatch.setattr(LangChainGeminiProvider, "generate", generate)
