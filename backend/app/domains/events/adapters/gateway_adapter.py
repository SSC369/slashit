"""Implements events' EventEmbeddingPort against the gateway (005 AD-7)."""

from uuid import UUID

from app.domains.gateway.public import Embedding, EmbedInteractor, EmbedPurpose


class GatewayEventEmbeddingAdapter:
    def __init__(self, *, embed_interactor: EmbedInteractor) -> None:
        self.embed_interactor = embed_interactor

    async def embed_event_text(
        self, *, user_id: UUID, text: str
    ) -> tuple[float, ...] | None:
        embed_result = await self.embed_interactor.embed(
            user_id=user_id, text=text, purpose=EmbedPurpose.DOCUMENT
        )
        if isinstance(embed_result, Embedding):
            return embed_result.vector
        return None
