"""The expenses domain's published surface, index §4.

Other domains reach expenses only through this class, re-exported from
``public.py`` and called through their own port and adapter (repo-rules.md
section 6). Reading, editing and deleting one expense are Records' own use
cases, in ``interactors/``; no other domain calls them, so they are not
published here (dev log D-2).
"""

from datetime import date
from uuid import UUID

import structlog

from app.domains.expenses.interfaces.dtos import (
    ExpenseCategory,
    ExpenseDTO,
    ExpenseFields,
)
from app.domains.expenses.interfaces.ports import ExpenseAnalyticsPort
from app.domains.expenses.interfaces.repositories import (
    ExpenseRepository,
    ExpenseWrite,
)

logger = structlog.get_logger(__name__)


class ExpenseService:
    def __init__(
        self,
        *,
        expense_repository: ExpenseRepository,
        analytics: ExpenseAnalyticsPort,
    ) -> None:
        self.expense_repository = expense_repository
        self.analytics = analytics

    async def create_expense(
        self, *, user_id: UUID, fields: ExpenseFields, original_input: str
    ) -> ExpenseDTO:
        """Save one expense capture has fully read. Capture has already checked
        the amount and the description; the table's checks back that up."""
        expense = await self.expense_repository.create_expense(
            user_id=user_id,
            write=ExpenseWrite(
                amount_paise=fields.amount_paise,
                description=fields.description,
                category=fields.category,
                spent_on=fields.spent_on,
                origin="command",
                original_input=original_input,
            ),
        )
        await self._record_saved(user_id=user_id)
        return expense

    async def list_expenses(
        self,
        *,
        user_id: UUID,
        category: ExpenseCategory | None,
        start: date | None,
        end: date | None,
    ) -> list[ExpenseDTO]:
        """Live expenses, newest ``spent_on`` first. Records' All tab passes no
        filter; slice 2's period filter passes a range."""
        return await self.expense_repository.list_for_user(
            user_id=user_id, category=category, start=start, end=end
        )

    async def _record_saved(self, *, user_id: UUID) -> None:
        """G1's metric. Never fails the save."""
        try:
            await self.analytics.record_expense_event(
                user_id=user_id, event_type="expense_saved"
            )
        except Exception:
            # Broad on purpose: an instrumentation loss is logged, never raised.
            logger.exception("expenses.event_not_recorded", user_id=str(user_id))
