"""Epic 006, sub-plan 4.3 §7: C-34 at the unit level. Expenses reach search
through their own port, typed as an expense, and an answer can describe one."""

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.domains.expenses.interfaces.dtos import (
    ExpenseCategory,
    ExpenseDTO,
    ExpenseSearchMatchDTO,
    ExpenseSearchPageDTO,
)
from app.domains.search.adapters.expenses_adapter import ExpenseSearchAdapter
from app.domains.search.interfaces.dtos import RecordType
from app.domains.search.services.answer_records import describe_record

USER = uuid.uuid4()
EXPENSE = ExpenseDTO(
    id=uuid.uuid4(),
    user_id=USER,
    amount_paise=85_050,
    description="Uber to office",
    category=ExpenseCategory.TRANSPORT,
    spent_on=date(2026, 10, 2),
    origin="command",
    original_input="/add-expense Uber to office 850.50",
    created_at=datetime(2026, 10, 2, tzinfo=UTC),
    updated_at=datetime(2026, 10, 2, tzinfo=UTC),
)


class _ExpenseService:
    def __init__(self) -> None:
        self.texts: list[str] = []

    async def search_candidates(
        self,
        *,
        user_id: uuid.UUID,
        text: str,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> ExpenseSearchPageDTO:
        self.texts.append(text)
        return ExpenseSearchPageDTO(
            matches=[
                ExpenseSearchMatchDTO(
                    expense=EXPENSE, all_terms=True, word_rank=1.0, distance=None
                )
            ],
            total=1,
        )

    async def embedding_of(
        self, *, user_id: uuid.UUID, expense_id: uuid.UUID
    ) -> tuple[float, ...] | None:
        return (0.5,) if expense_id == EXPENSE.id else None


async def test_the_adapter_passes_the_search_text_and_types_each_match() -> None:
    service = _ExpenseService()
    adapter = ExpenseSearchAdapter(expense_service=service)  # type: ignore[arg-type]

    page = await adapter.search_candidates(
        user_id=USER,
        text="₹850.50",
        terms=["850", "50"],
        query_embedding=None,
        max_distance=0.5,
        limit=10,
    )

    assert adapter.record_type == RecordType.EXPENSE
    assert service.texts == ["₹850.50"]
    assert page.total == 1
    candidate = page.candidates[0]
    assert candidate.record_type == RecordType.EXPENSE
    assert candidate.record_id == EXPENSE.id
    assert candidate.all_terms is True
    assert await adapter.embedding_of(user_id=USER, record_id=EXPENSE.id) == (0.5,)


def test_an_answer_reads_an_expense_by_amount_day_and_category() -> None:
    """005 FR-16: so "how much was the uber" is answerable from the record."""
    described = describe_record(
        number=1,
        record_type=RecordType.EXPENSE,
        item=EXPENSE,
        timezone=ZoneInfo("Asia/Kolkata"),
    )

    assert described.text == "Uber to office"
    assert described.detail == "expense, ₹850.50 on Fri 02 Oct 2026, transport"
