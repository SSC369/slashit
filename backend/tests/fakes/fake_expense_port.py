"""In-memory stand-ins for capture's ExpensePort and LocalClockPort, and
records' ExpenseRecordsPort."""

import uuid
from datetime import UTC, date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domains.capture.services.expense_capture import ExpenseCaptureService
from app.domains.expenses.public import ExpenseCategory, ExpenseDTO, ExpenseFields
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
