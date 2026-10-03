"""Give one expense its meaning vector. Run by `expenses.embed_expense`."""

from app.domains.expenses.interactors.dtos import EmbedExpenseInputDTO
from app.domains.expenses.interfaces.ports import ExpenseEmbeddingPort
from app.domains.expenses.interfaces.repositories import ExpenseRepository


class EmbedExpenseFailedError(Exception):
    """The model refused. Raised so the job's retry strategy runs again; after
    the last attempt the vector stays NULL for the periodic backfill."""


class EmbedExpenseInteractor:
    def __init__(
        self,
        *,
        expense_repository: ExpenseRepository,
        embedding: ExpenseEmbeddingPort,
    ) -> None:
        self.expense_repository = expense_repository
        self.embedding = embedding

    async def embed_expense(self, *, dto: EmbedExpenseInputDTO) -> bool:
        """Embed the expense's current description and store it. False when
        there is nothing to do: gone, already embedded, or edited while the
        model ran (the next queued embed covers that).

        Raises:
            EmbedExpenseFailedError: the model refused.
        """
        description = await self.expense_repository.get_description_needing_embedding(
            user_id=dto.user_id, expense_id=dto.expense_id
        )
        if description is None:
            return False
        vector = await self.embedding.embed_expense_description(
            user_id=dto.user_id, description=description
        )
        if vector is None:
            raise EmbedExpenseFailedError()
        return await self.expense_repository.set_embedding(
            user_id=dto.user_id,
            expense_id=dto.expense_id,
            description=description,
            embedding=vector,
        )
