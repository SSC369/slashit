"""FR-21: edit an expense's amount, description, category or date."""

from dataclasses import replace

import structlog

from app.domains.expenses.constants import MAX_AMOUNT_PAISE, MAX_DESCRIPTION_LENGTH
from app.domains.expenses.graphql.errors import (
    ExpenseField,
    ExpenseInvalidError,
    ExpenseInvalidReason,
    ExpenseNotFoundError,
)
from app.domains.expenses.interactors.dtos import UpdateExpenseInputDTO
from app.domains.expenses.interfaces.dtos import ExpenseChanges, ExpenseDTO
from app.domains.expenses.interfaces.ports import (
    ExpenseAnalyticsPort,
    ExpenseEventType,
)
from app.domains.expenses.interfaces.repositories import ExpenseRepository

logger = structlog.get_logger(__name__)


class UpdateExpenseInteractor:
    def __init__(
        self,
        *,
        expense_repository: ExpenseRepository,
        analytics: ExpenseAnalyticsPort,
    ) -> None:
        self.expense_repository = expense_repository
        self.analytics = analytics

    async def update_expense(self, *, dto: UpdateExpenseInputDTO) -> ExpenseDTO:
        """Apply the changed fields to one live expense.

        A description edit leaves the category as it was (FR-21). Any date is
        accepted, past or future, with no further question.

        Raises:
            ExpenseInvalidError: the amount is not above zero, or the
                description is empty or over 200 characters.
            ExpenseNotFoundError: no live expense with this id is theirs.
        """
        changes = self._trim_description(changes=dto.changes)
        self._validate_amount(amount_paise=changes.amount_paise)
        self._validate_description(description=changes.description)

        previous = await self.expense_repository.get_by_id(
            user_id=dto.user_id, expense_id=dto.expense_id
        )
        updated = await self.expense_repository.update_expense(
            user_id=dto.user_id, expense_id=dto.expense_id, changes=changes
        )
        if previous is None or updated is None:
            raise ExpenseNotFoundError()
        await self._record_edit_events(dto=dto, previous=previous, updated=updated)
        return updated

    def _trim_description(self, *, changes: ExpenseChanges) -> ExpenseChanges:
        if changes.description is None:
            return changes
        return replace(changes, description=changes.description.strip())

    def _validate_amount(self, *, amount_paise: int | None) -> None:
        if amount_paise is not None and amount_paise <= 0:
            raise ExpenseInvalidError(
                field=ExpenseField.AMOUNT, reason=ExpenseInvalidReason.NOT_POSITIVE
            )
        if amount_paise is not None and amount_paise > MAX_AMOUNT_PAISE:
            raise ExpenseInvalidError(
                field=ExpenseField.AMOUNT, reason=ExpenseInvalidReason.TOO_LARGE
            )

    def _validate_description(self, *, description: str | None) -> None:
        if description is None:
            return
        if not description:
            raise ExpenseInvalidError(
                field=ExpenseField.DESCRIPTION, reason=ExpenseInvalidReason.EMPTY
            )
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise ExpenseInvalidError(
                field=ExpenseField.DESCRIPTION,
                reason=ExpenseInvalidReason.TOO_LONG,
                length=len(description),
            )

    async def _record_edit_events(
        self, *, dto: UpdateExpenseInputDTO, previous: ExpenseDTO, updated: ExpenseDTO
    ) -> None:
        """G3 and G4's metrics: an amount or a category the user corrected."""
        if previous.amount_paise != updated.amount_paise:
            await self._record_event(dto=dto, event_type="expense_amount_edited")
        if previous.category != updated.category:
            await self._record_event(dto=dto, event_type="expense_category_edited")

    async def _record_event(
        self, *, dto: UpdateExpenseInputDTO, event_type: ExpenseEventType
    ) -> None:
        try:
            await self.analytics.record_expense_event(
                user_id=dto.user_id, event_type=event_type
            )
        except Exception:
            # Broad on purpose: an instrumentation loss is logged, never raised.
            logger.exception("expenses.event_not_recorded", user_id=str(dto.user_id))
