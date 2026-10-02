"""FR-22: delete from the detail. Soft, per ``product.md`` §4."""

import structlog

from app.domains.expenses.graphql.errors import ExpenseNotFoundError
from app.domains.expenses.interactors.dtos import DeleteExpenseInputDTO
from app.domains.expenses.interfaces.ports import ExpenseAnalyticsPort
from app.domains.expenses.interfaces.repositories import ExpenseRepository

logger = structlog.get_logger(__name__)


class DeleteExpenseInteractor:
    def __init__(
        self,
        *,
        expense_repository: ExpenseRepository,
        analytics: ExpenseAnalyticsPort,
    ) -> None:
        self.expense_repository = expense_repository
        self.analytics = analytics

    async def delete_expense(self, *, dto: DeleteExpenseInputDTO) -> None:
        """Stamp the expense deleted, so it leaves every view, count and total.

        Raises:
            ExpenseNotFoundError: no live expense with this id is theirs,
                including one already deleted.
        """
        deleted = await self.expense_repository.soft_delete(
            user_id=dto.user_id, expense_id=dto.expense_id
        )
        if not deleted:
            raise ExpenseNotFoundError()
        await self._record_deleted(dto=dto)

    async def _record_deleted(self, *, dto: DeleteExpenseInputDTO) -> None:
        try:
            await self.analytics.record_expense_event(
                user_id=dto.user_id, event_type="expense_deleted"
            )
        except Exception:
            # Broad on purpose: an instrumentation loss is logged, never raised.
            logger.exception("expenses.event_not_recorded", user_id=str(dto.user_id))
