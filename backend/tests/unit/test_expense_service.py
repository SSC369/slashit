"""Epic 006, sub-plan 4.1: the published service capture and records use."""

import uuid
from datetime import date

from app.domains.expenses.interfaces.dtos import ExpenseCategory, ExpenseFields
from app.domains.expenses.services.expense_service import ExpenseService
from tests.fakes.fake_expense_analytics_port import FakeExpenseAnalyticsPort
from tests.fakes.fake_expense_repository import FakeExpenseRepository

USER = uuid.uuid4()


class FailingAnalytics:
    async def record_expense_event(
        self, *, user_id: uuid.UUID, event_type: str
    ) -> None:
        raise RuntimeError("events table unavailable")


async def test_create_saves_from_a_command_and_records_the_save() -> None:
    """G1's metric: one event per save, with no text or amount in it."""
    repository = FakeExpenseRepository()
    analytics = FakeExpenseAnalyticsPort()
    service = ExpenseService(expense_repository=repository, analytics=analytics)

    expense = await service.create_expense(
        user_id=USER,
        fields=ExpenseFields(
            amount_paise=85_000,
            description="dinner",
            category=ExpenseCategory.FOOD,
            spent_on=date(2026, 10, 1),
        ),
        original_input="/add-expense ₹850 dinner yesterday",
    )

    assert expense.origin == "command"
    assert expense.original_input == "/add-expense ₹850 dinner yesterday"
    assert analytics.events == ["expense_saved"]
    assert await service.list_expenses(
        user_id=USER, category=None, start=None, end=None
    ) == [expense]


async def test_a_lost_event_never_fails_the_save() -> None:
    repository = FakeExpenseRepository()
    service = ExpenseService(
        expense_repository=repository, analytics=FailingAnalytics()
    )

    await service.create_expense(
        user_id=USER,
        fields=ExpenseFields(
            amount_paise=100,
            description="tea",
            category=ExpenseCategory.FOOD,
            spent_on=date(2026, 10, 2),
        ),
        original_input="/add-expense 1 tea",
    )

    assert len(repository.rows) == 1
