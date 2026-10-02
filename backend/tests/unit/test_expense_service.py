"""Epic 006, sub-plan 4.1: the published service capture and records use."""

import uuid
from datetime import date

from app.domains.expenses.interfaces.dtos import (
    ExpenseCategory,
    ExpenseFields,
    PeriodNotUnderstood,
)
from app.domains.expenses.services.expense_service import ExpenseService
from tests.fakes.fake_expense_analytics_port import FakeExpenseAnalyticsPort
from tests.fakes.fake_expense_repository import FakeExpenseRepository
from tests.fakes.fake_local_date_port import FakeLocalDatePort

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
    service = ExpenseService(
        expense_repository=repository,
        analytics=analytics,
        local_date=FakeLocalDatePort(today=date(2026, 10, 2)),
    )

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
        expense_repository=repository,
        analytics=FailingAnalytics(),
        local_date=FakeLocalDatePort(today=date(2026, 10, 2)),
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


# --- Sub-plan 4.2: summaries ---

TODAY = date(2026, 10, 2)


def _summary_service(
    *, repository: FakeExpenseRepository, analytics: FakeExpenseAnalyticsPort
) -> ExpenseService:
    return ExpenseService(
        expense_repository=repository,
        analytics=analytics,
        local_date=FakeLocalDatePort(today=TODAY),
    )


async def _save(
    *,
    service: ExpenseService,
    paise: int,
    category: ExpenseCategory,
    spent_on: date,
    user_id: uuid.UUID = USER,
) -> None:
    await service.create_expense(
        user_id=user_id,
        fields=ExpenseFields(
            amount_paise=paise,
            description="spend",
            category=category,
            spent_on=spent_on,
        ),
        original_input="/add-expense spend",
    )


async def test_totals_are_exact_largest_first_and_leave_out_empty_categories() -> None:
    """C-27 and C-28, unit. A tie falls back to FR-9's order."""
    repository = FakeExpenseRepository()
    analytics = FakeExpenseAnalyticsPort()
    service = _summary_service(repository=repository, analytics=analytics)
    for paise, category in [
        (1, ExpenseCategory.BILLS),
        (99_99_99_999_99, ExpenseCategory.TRAVEL),
        (85_050, ExpenseCategory.FOOD),
        (85_050, ExpenseCategory.TRANSPORT),
    ]:
        await _save(service=service, paise=paise, category=category, spent_on=TODAY)
    await _save(
        service=service,
        paise=500,
        category=ExpenseCategory.HEALTH,
        spent_on=date(2026, 9, 30),
    )

    summary = await service.summarise_text(user_id=USER, text="this month")

    assert not isinstance(summary, PeriodNotUnderstood)
    assert [(total.category, total.total_paise) for total in summary.totals] == [
        (ExpenseCategory.TRAVEL, 99_99_99_999_99),
        (ExpenseCategory.FOOD, 85_050),
        (ExpenseCategory.TRANSPORT, 85_050),
        (ExpenseCategory.BILLS, 1),
    ]
    assert summary.grand_total_paise == 99_99_99_999_99 + 85_050 * 2 + 1
    assert summary.count == 4
    assert (summary.label, summary.phrase) == ("October 2026 so far", "this month")
    assert analytics.summaries_viewed == [True]


async def test_a_period_off_the_list_is_not_understood_and_records_nothing() -> None:
    """FR-27."""
    analytics = FakeExpenseAnalyticsPort()
    service = _summary_service(repository=FakeExpenseRepository(), analytics=analytics)

    outcome = await service.summarise_text(user_id=USER, text=" since diwali ")

    assert outcome == PeriodNotUnderstood(text="since diwali")
    assert analytics.summaries_viewed == []


async def test_an_empty_period_has_no_totals_and_a_count_of_zero() -> None:
    """FR-26."""
    service = _summary_service(
        repository=FakeExpenseRepository(), analytics=FakeExpenseAnalyticsPort()
    )

    summary = await service.summarise_text(user_id=USER, text="last week")

    assert not isinstance(summary, PeriodNotUnderstood)
    assert (summary.totals, summary.count, summary.grand_total_paise) == ([], 0, 0)
    assert (summary.start, summary.end) == (date(2026, 9, 21), date(2026, 9, 27))


async def test_the_band_and_the_command_agree_for_the_same_period() -> None:
    """FR-28, unit: a picker range sums as its typed period does, and takes
    its label."""
    repository = FakeExpenseRepository()
    analytics = FakeExpenseAnalyticsPort()
    service = _summary_service(repository=repository, analytics=analytics)
    await _save(
        service=service,
        paise=1_000,
        category=ExpenseCategory.FOOD,
        spent_on=date(2026, 9, 3),
    )
    await _save(
        service=service,
        paise=2_000,
        category=ExpenseCategory.FOOD,
        spent_on=date(2026, 9, 3),
        user_id=uuid.uuid4(),
    )
    last_month = next(
        period
        for period in await service.periods(user_id=USER)
        if period.label == "September 2026"
    )

    typed = await service.summarise_text(user_id=USER, text="last month")
    picked = await service.summarise(
        user_id=USER, start=last_month.start, end=last_month.end, category=None
    )

    assert typed == picked
    assert picked.grand_total_paise == 1_000
    assert analytics.summaries_viewed == [True, False]


async def test_all_time_and_a_category_filter_sum_without_a_range() -> None:
    """Decision 2A and FR-17."""
    repository = FakeExpenseRepository()
    service = _summary_service(
        repository=repository, analytics=FakeExpenseAnalyticsPort()
    )
    await _save(
        service=service,
        paise=300,
        category=ExpenseCategory.FOOD,
        spent_on=date(2024, 1, 1),
    )
    await _save(
        service=service, paise=700, category=ExpenseCategory.BILLS, spent_on=TODAY
    )

    summary = await service.summarise(
        user_id=USER, start=None, end=None, category=ExpenseCategory.FOOD
    )

    assert summary.label == "All time"
    assert summary.grand_total_paise == 300
    assert summary.category == ExpenseCategory.FOOD
