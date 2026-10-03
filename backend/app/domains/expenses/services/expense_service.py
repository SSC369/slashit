"""The expenses domain's published surface, index §4.

Other domains reach expenses only through this class, re-exported from
``public.py`` and called through their own port and adapter (repo-rules.md
section 6). Reading, editing and deleting one expense are Records' own use
cases, in ``interactors/``; no other domain calls them, so they are not
published here (dev log D-2).
"""

from collections.abc import Sequence
from datetime import date
from uuid import UUID

import structlog

from app.domains.expenses.constants import EXPENSE_CATEGORIES
from app.domains.expenses.interfaces.dtos import (
    CategoryTotal,
    ExpenseCategory,
    ExpenseDTO,
    ExpenseFields,
    ExpenseSearchPageDTO,
    ExpenseSummaryDTO,
    Period,
    PeriodKey,
    PeriodNotUnderstood,
)
from app.domains.expenses.interfaces.ports import (
    ExpenseAnalyticsPort,
    ExpenseEmbedQueue,
    LocalDatePort,
)
from app.domains.expenses.interfaces.repositories import (
    ExpenseRepository,
    ExpenseWrite,
)
from app.domains.expenses.services.periods import parse_period, picker_periods
from app.domains.expenses.services.search_amount import amount_from_search

logger = structlog.get_logger(__name__)


class ExpenseService:
    def __init__(
        self,
        *,
        expense_repository: ExpenseRepository,
        analytics: ExpenseAnalyticsPort,
        local_date: LocalDatePort,
        embed_queue: ExpenseEmbedQueue,
    ) -> None:
        self.expense_repository = expense_repository
        self.analytics = analytics
        self.local_date = local_date
        self.embed_queue = embed_queue

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
        # Sub-plan 4.3: searchable by meaning once the job runs (005 AD-7).
        await self.embed_queue.queue_expense_embed(
            user_id=user_id, expense_id=expense.id, delay_seconds=0
        )
        return expense

    async def search_candidates(
        self,
        *,
        user_id: UUID,
        text: str,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> ExpenseSearchPageDTO:
        """Sub-plan 4.3: the user's live expenses a search matches, by words,
        meaning, or the whole search read as one exact amount (FR-30, Q1).
        Ranking is search's, not decided here (005 AD-1)."""
        return await self.expense_repository.search_expenses(
            user_id=user_id,
            terms=terms,
            amount_paise=amount_from_search(text=text),
            query_embedding=query_embedding,
            max_distance=max_distance,
            limit=limit,
        )

    async def embedding_of(
        self, *, user_id: UUID, expense_id: UUID
    ) -> tuple[float, ...] | None:
        """The live expense's stored vector, for related records (005 AD-6)."""
        return await self.expense_repository.get_embedding(
            user_id=user_id, expense_id=expense_id
        )

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

    async def periods(self, *, user_id: UUID) -> list[Period]:
        """The Records picker's periods, resolved in the user's zone by the
        parser ``/expenses`` uses (sub-plan 4.2, decision 3A)."""
        today = await self.local_date.local_today(user_id=user_id)
        return picker_periods(today=today)

    async def summarise(
        self,
        *,
        user_id: UUID,
        start: date | None,
        end: date | None,
        category: ExpenseCategory | None,
    ) -> ExpenseSummaryDTO:
        """FR-18: the Records band's totals for the picked range. The label is
        the picker period with that range; the client sends no other."""
        today = await self.local_date.local_today(user_id=user_id)
        period = _picker_period_for(start=start, end=end, today=today)
        summary = await self._summarise_period(
            user_id=user_id, period=period, category=category
        )
        await self._record_summary_viewed(user_id=user_id, from_command=False)
        return summary

    async def summarise_text(
        self, *, user_id: UUID, text: str
    ) -> ExpenseSummaryDTO | PeriodNotUnderstood:
        """FR-23, FR-24 and FR-27: ``/expenses <period>``. No model call."""
        today = await self.local_date.local_today(user_id=user_id)
        period = parse_period(text=text, today=today)
        if period is None:
            return PeriodNotUnderstood(text=text.strip())
        summary = await self._summarise_period(
            user_id=user_id, period=period, category=None
        )
        await self._record_summary_viewed(user_id=user_id, from_command=True)
        return summary

    async def _summarise_period(
        self, *, user_id: UUID, period: Period, category: ExpenseCategory | None
    ) -> ExpenseSummaryDTO:
        totals = await self.expense_repository.sum_by_category(
            user_id=user_id, start=period.start, end=period.end, category=category
        )
        return ExpenseSummaryDTO(
            label=period.label,
            phrase=period.phrase,
            start=period.start,
            end=period.end,
            category=category,
            totals=_largest_first(totals=totals),
            grand_total_paise=sum(total.total_paise for total in totals),
            count=sum(total.count for total in totals),
        )

    async def _record_summary_viewed(
        self, *, user_id: UUID, from_command: bool
    ) -> None:
        """G2's metric. Never fails the summary."""
        try:
            await self.analytics.record_summary_viewed(
                user_id=user_id, from_command=from_command
            )
        except Exception:
            # Broad on purpose: an instrumentation loss is logged, never raised.
            logger.exception("expenses.event_not_recorded", user_id=str(user_id))

    async def _record_saved(self, *, user_id: UUID) -> None:
        """G1's metric. Never fails the save."""
        try:
            await self.analytics.record_expense_event(
                user_id=user_id, event_type="expense_saved"
            )
        except Exception:
            # Broad on purpose: an instrumentation loss is logged, never raised.
            logger.exception("expenses.event_not_recorded", user_id=str(user_id))


def _largest_first(*, totals: list[CategoryTotal]) -> list[CategoryTotal]:
    """FR-25: largest first; a tie keeps FR-9's category order."""
    return sorted(
        totals,
        key=lambda total: (
            -total.total_paise,
            EXPENSE_CATEGORIES.index(total.category.value),
        ),
    )


def _picker_period_for(*, start: date | None, end: date | None, today: date) -> Period:
    """The picker period holding this range, for its label. A range the picker
    never offers is still summed, labelled by its dates."""
    for period in picker_periods(today=today):
        if (period.start, period.end) == (start, end):
            return period
    label = f"{start} to {end}"
    return Period(
        key=PeriodKey.MONTH, start=start, end=end, label=label, phrase=f"from {label}"
    )
