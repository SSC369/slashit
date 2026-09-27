"""What a model provider must do.

`ExtractInteractor` depends on this and on nothing concrete. LangChain lives
below it, inside `services/`, and no name from LangChain appears above this line.
Rule T4 of the tech stack requires the boundary to be ours; moving off LangChain
is then one file.
"""

from typing import Protocol

from app.domains.gateway.interfaces.dtos import (
    ExtractionRequest,
    ProviderEmbedding,
    ProviderResult,
)


class ModelProvider(Protocol):
    async def generate(self, request: ExtractionRequest) -> ProviderResult:
        """Return a structured result, or raise a gateway error.

        Raises:
            SharedQuotaExhaustedError: the provider refused on quota.
            ProviderUnavailableError: outage or connection failure.
            ProviderTimeoutError: exceeded the time budget.
            MalformedResultError: the response did not match the schema.
        """
        ...

    async def embed(self, *, text: str) -> ProviderEmbedding:
        """Return the meaning vector for one text. Epic 004.

        Raises:
            SharedQuotaExhaustedError: the provider refused on quota.
            ProviderUnavailableError: outage or connection failure.
            ProviderTimeoutError: exceeded the time budget.
        """
        ...
