"""A ModelProvider that returns or raises on command."""

from app.domains.gateway.constants import EMBEDDING_DIMENSIONS, EmbedPurpose
from app.domains.gateway.interfaces.dtos import (
    ExtractionRequest,
    ProviderEmbedding,
    ProviderResult,
)


class FakeProvider:
    def __init__(
        self, result: ProviderResult | None = None, raises: Exception | None = None
    ) -> None:
        self._result = result
        self._raises = raises
        self.calls = 0
        self.purposes: list[EmbedPurpose] = []

    async def generate(self, request: ExtractionRequest) -> ProviderResult:
        self.calls += 1
        if self._raises is not None:
            raise self._raises
        assert self._result is not None
        return self._result

    async def embed(self, *, text: str, purpose: EmbedPurpose) -> ProviderEmbedding:
        self.calls += 1
        self.purposes.append(purpose)
        if self._raises is not None:
            raise self._raises
        return ProviderEmbedding(
            vector=tuple(0.0 for _ in range(EMBEDDING_DIMENSIONS)), model="fake-embed"
        )
