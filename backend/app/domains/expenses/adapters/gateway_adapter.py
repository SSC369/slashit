"""Implements expenses' ExpenseEmbeddingPort against the gateway (sub-plan 4.3)."""

from uuid import UUID

from app.domains.gateway.public import Embedding, EmbedInteractor, EmbedPurpose


class GatewayExpenseEmbeddingAdapter:
    def __init__(self, *, embed_interactor: EmbedInteractor) -> None:
        self.embed_interactor = embed_interactor

    async def embed_expense_description(
        self, *, user_id: UUID, description: str
    ) -> tuple[float, ...] | None:
        # A stored record is a document, a search is a query (005 D-22).
        embed_result = await self.embed_interactor.embed(
            user_id=user_id, text=description, purpose=EmbedPurpose.DOCUMENT
        )
        if isinstance(embed_result, Embedding):
            return embed_result.vector
        return None
