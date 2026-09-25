"""The gateway's second use case: turn one text into a meaning vector. Epic 004.

Three steps: kill switch, provider, usage. There is no allowance step. Tech
stack rule T9: embeddings are attributed to the user in ``ai_usage`` but never
counted against the per-user request cap, so this interactor has no
``UserLimitReached`` outcome to return.
"""

import time
import uuid
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import structlog

from app.core.errors import DomainError
from app.core.settings import Settings
from app.domains.gateway.constants import PROVIDER_NAME
from app.domains.gateway.errors import (
    MalformedResultError,
    ProviderTimeout,
    ProviderTimeoutError,
    ProviderUnavailable,
    ProviderUnavailableError,
    SharedQuotaExhausted,
    SharedQuotaExhaustedError,
)
from app.domains.gateway.interfaces.dtos import Embedding, UsageRecord
from app.domains.gateway.interfaces.providers import ModelProvider
from app.domains.gateway.interfaces.repositories import UsageRepository

logger = structlog.get_logger(__name__)

EmbedResult = Embedding | ProviderUnavailable | ProviderTimeout | SharedQuotaExhausted

_OUTCOME_BY_ERROR: dict[type[DomainError], str] = {
    SharedQuotaExhaustedError: "shared_quota_exhausted",
    ProviderUnavailableError: "provider_unavailable",
    ProviderTimeoutError: "provider_timeout",
    MalformedResultError: "malformed_result",
}


class EmbedInteractor:
    def __init__(
        self,
        *,
        provider: ModelProvider,
        usage_repository: UsageRepository,
        settings: Settings,
    ) -> None:
        self.provider = provider
        self.usage_repository = usage_repository
        self.settings = settings

    async def embed(self, *, user_id: UUID, text: str) -> EmbedResult:
        """Embed one text on behalf of one user.

        Every provider failure is returned as its union member, never raised,
        mirroring ``ExtractInteractor``.
        """
        try:
            self._validate_gateway_enabled()
        except ProviderUnavailableError as error:
            return cast(EmbedResult, error.to_gql())

        started = time.perf_counter()
        try:
            embedding = await self.provider.embed(text=text)
        except DomainError as error:
            await self._record_embed_usage(
                user_id=user_id, error=error, started=started
            )
            return cast(EmbedResult, error.to_gql())

        await self._record_embed_usage(user_id=user_id, error=None, started=started)
        return Embedding(vector=embedding.vector, model=embedding.model)

    def _validate_gateway_enabled(self) -> None:
        """The same kill switch the extraction path honours."""
        if not self.settings.gateway_enabled:
            raise ProviderUnavailableError()

    async def _record_embed_usage(
        self, *, user_id: UUID, error: DomainError | None, started: float
    ) -> None:
        """Write the usage row with ``operation = embed``. Never raises, for
        the reason ``ExtractInteractor._record_usage`` gives."""
        outcome = "success" if error is None else _OUTCOME_BY_ERROR[type(error)]
        usage = UsageRecord(
            id=uuid.uuid4(),
            user_id=user_id,
            provider=PROVIDER_NAME,
            model=self.settings.gemini_embedding_model,
            input_tokens=0,
            output_tokens=0,
            outcome=outcome,
            latency_ms=int((time.perf_counter() - started) * 1000),
            operation="embed",
        )
        try:
            await self.usage_repository.record(
                usage=usage, occurred_at=datetime.now(UTC)
            )
        except Exception:
            logger.exception(
                "gateway.usage_not_recorded", user_id=str(user_id), outcome=outcome
            )
