"""Implements records' TaskEmbeddingPort against the gateway (005 AD-7)."""

from uuid import UUID

from app.domains.gateway.public import Embedding, EmbedInteractor


class GatewayTaskEmbeddingAdapter:
    def __init__(self, *, embed_interactor: EmbedInteractor) -> None:
        self.embed_interactor = embed_interactor

    async def embed_task_title(
        self, *, user_id: UUID, title: str
    ) -> tuple[float, ...] | None:
        embed_result = await self.embed_interactor.embed(user_id=user_id, text=title)
        if isinstance(embed_result, Embedding):
            return embed_result.vector
        return None
