"""Implements reminders' ReminderEmbeddingPort against the gateway (005 AD-7)."""

from uuid import UUID

from app.domains.gateway.public import Embedding, EmbedInteractor


class GatewayReminderEmbeddingAdapter:
    def __init__(self, *, embed_interactor: EmbedInteractor) -> None:
        self.embed_interactor = embed_interactor

    async def embed_reminder_description(
        self, *, user_id: UUID, description: str
    ) -> tuple[float, ...] | None:
        embed_result = await self.embed_interactor.embed(
            user_id=user_id, text=description
        )
        if isinstance(embed_result, Embedding):
            return embed_result.vector
        return None
