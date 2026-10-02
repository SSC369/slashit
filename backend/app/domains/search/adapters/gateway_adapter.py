"""Implements search's QueryEmbeddingPort against the gateway (AD-4)."""

import asyncio
from uuid import UUID

import structlog

from app.domains.gateway.public import Embedding, EmbedInteractor, EmbedPurpose

logger = structlog.get_logger(__name__)


class GatewayQueryEmbeddingAdapter:
    def __init__(
        self, *, embed_interactor: EmbedInteractor, timeout_seconds: float
    ) -> None:
        self.embed_interactor = embed_interactor
        self.timeout_seconds = timeout_seconds

    async def embed_query(
        self, *, user_id: UUID, text: str
    ) -> tuple[float, ...] | None:
        """None on a timeout, a provider error or an exhausted quota, so the
        search falls back to words (FR-20). An embed is never counted against
        the per-user cap (T9), so it is never refused for that."""
        try:
            embed_result = await asyncio.wait_for(
                self.embed_interactor.embed(
                    user_id=user_id, text=text, purpose=EmbedPurpose.QUERY
                ),
                timeout=self.timeout_seconds,
            )
        except TimeoutError:
            logger.warning("search.query_embed_timeout")
            return None
        if isinstance(embed_result, Embedding):
            return embed_result.vector
        logger.warning("search.query_embed_refused", result=type(embed_result).__name__)
        return None
