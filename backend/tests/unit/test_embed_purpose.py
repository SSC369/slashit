"""Epic 005 D-22: a saved record is embedded as a document, a search as a query."""

import uuid

import pytest

from app.core.settings import get_settings
from app.domains.gateway.constants import EmbedPurpose
from app.domains.gateway.interactors.embed import EmbedInteractor
from app.domains.gateway.services.langchain_provider import LangChainGeminiProvider
from tests.fakes.fake_provider import FakeProvider
from tests.fakes.fake_usage_repository import FakeUsageRepository


class _RecordingEmbeddings:
    """Stands in for the LangChain binding and keeps each task type asked for."""

    def __init__(self) -> None:
        self.task_types: list[str | None] = []

    async def aembed_query(
        self, text: str, *, task_type: str | None, output_dimensionality: int
    ) -> list[float]:
        self.task_types.append(task_type)
        return [0.0] * output_dimensionality


class _Provider(LangChainGeminiProvider):
    """The real embed mapping, with the network replaced."""

    def __init__(self, embeddings: _RecordingEmbeddings) -> None:
        self._embeddings = embeddings  # type: ignore[assignment]
        self._embedding_model_name = "test-embed"


@pytest.mark.parametrize(
    ("purpose", "task_type"),
    [
        (EmbedPurpose.DOCUMENT, "RETRIEVAL_DOCUMENT"),
        (EmbedPurpose.QUERY, "RETRIEVAL_QUERY"),
    ],
)
async def test_each_purpose_asks_the_provider_for_its_own_task_type(
    purpose: EmbedPurpose, task_type: str
) -> None:
    embeddings = _RecordingEmbeddings()

    await _Provider(embeddings).embed(text="renew passport", purpose=purpose)

    assert embeddings.task_types == [task_type]


async def test_the_interactor_passes_the_purpose_through() -> None:
    provider = FakeProvider()
    interactor = EmbedInteractor(
        provider=provider,
        usage_repository=FakeUsageRepository(limit=20, used=0),
        settings=get_settings(),
    )

    await interactor.embed(
        user_id=uuid.uuid4(), text="passport", purpose=EmbedPurpose.QUERY
    )

    assert provider.purposes == [EmbedPurpose.QUERY]
