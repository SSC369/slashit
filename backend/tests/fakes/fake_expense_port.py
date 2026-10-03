"""In-memory stand-ins for capture's ExpensePort and LocalClockPort, and
records' ExpenseRecordsPort."""

import uuid
from datetime import UTC, date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domains.capture.services.expense_capture import ExpenseCaptureService
from app.domains.expenses.interfaces.dtos import CategoryTotal
from app.domains.expenses.public import (
    ExpenseCategory,
    ExpenseDTO,
    ExpenseFields,
    ExpenseSummaryDTO,
    PeriodNotUnderstood,
)
from app.domains.expenses.services.periods import parse_period
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_extraction_port import FakeExtractionPort

# A Friday, the design's "today" (02-design.md, header).
TODAY = date(2026, 10, 2)


def make_expense(
    *,
    user_id: UUID,
    amount_paise: int = 85_000,
    description: str = "dinner with friends",
    category: ExpenseCategory = ExpenseCategory.FOOD,
    spent_on: date = TODAY,
    created_at: datetime | None = None,
) -> ExpenseDTO:
    moment = created_at or datetime.now(UTC)
    return ExpenseDTO(
        id=uuid.uuid4(),
        user_id=user_id,
        amount_paise=amount_paise,
        description=description,
        category=category,
        spent_on=spent_on,
        origin="command",
        original_input=f"/add-expense {description}",
        created_at=moment,
        updated_at=moment,
    )


class FakeExpensePort:
    """Saves into a list, as expenses' published service would."""

    def __init__(self) -> None:
        self.saved: list[ExpenseDTO] = []
        self.original_inputs: list[str] = []
        self.summarised_texts: list[str] = []

    async def create_expense(
        self, *, user_id: UUID, fields: ExpenseFields, original_input: str
    ) -> ExpenseDTO:
        expense = ExpenseDTO(
            id=uuid.uuid4(),
            user_id=user_id,
            amount_paise=fields.amount_paise,
            description=fields.description,
            category=fields.category,
            spent_on=fields.spent_on,
            origin="command",
            original_input=original_input,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.saved.append(expense)
        self.original_inputs.append(original_input)
        return expense

    async def summarise_text(
        self, *, user_id: UUID, text: str
    ) -> ExpenseSummaryDTO | PeriodNotUnderstood:
        """Reads the period as expenses does and sums what this fake saved,
        without ordering: the order is expenses' rule, tested there."""
        self.summarised_texts.append(text)
        period = parse_period(text=text, today=TODAY)
        if period is None:
            return PeriodNotUnderstood(text=text.strip())
        in_period = [
            expense
            for expense in self.saved
            if expense.user_id == user_id
            and period.start is not None
            and period.end is not None
            and period.start <= expense.spent_on <= period.end
        ]
        totals = [
            CategoryTotal(
                category=category,
                total_paise=sum(
                    expense.amount_paise
                    for expense in in_period
                    if expense.category == category
                ),
                count=sum(1 for expense in in_period if expense.category == category),
            )
            for category in {expense.category for expense in in_period}
        ]
        return ExpenseSummaryDTO(
            label=period.label,
            phrase=period.phrase,
            start=period.start,
            end=period.end,
            category=None,
            totals=totals,
            grand_total_paise=sum(expense.amount_paise for expense in in_period),
            count=len(in_period),
        )


class FakeLocalClock:
    """The user's local now: noon on ``today`` in Kolkata."""

    def __init__(self, *, today: date = TODAY) -> None:
        self.today = today

    async def local_now(self, *, user_id: UUID) -> tuple[datetime, str]:
        zone = "Asia/Kolkata"
        return datetime(
            self.today.year, self.today.month, self.today.day, 12, tzinfo=ZoneInfo(zone)
        ), zone


class FakeExpenseRecordsPort:
    def __init__(self, *, expenses: list[ExpenseDTO] | None = None) -> None:
        self.expenses = list(expenses or [])

    async def list_expenses(self, *, user_id: UUID) -> list[ExpenseDTO]:
        return [expense for expense in self.expenses if expense.user_id == user_id]


def fake_expense_capture(
    *,
    extraction: FakeExtractionPort | None = None,
    expense_port: FakeExpensePort | None = None,
    analytics: FakeAnalyticsPort | None = None,
    today: date = TODAY,
) -> ExpenseCaptureService:
    return ExpenseCaptureService(
        expense_port=expense_port or FakeExpensePort(),
        extraction=extraction or FakeExtractionPort(),
        local_clock=FakeLocalClock(today=today),
        analytics=analytics or FakeAnalyticsPort(),
    )
