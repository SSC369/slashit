"""Epic 006, sub-plan 4.1 §7: C-14 to C-16. Records' list, detail, edit and
delete, against an in-memory repository."""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest

from app.domains.expenses.graphql.errors import (
    ExpenseField,
    ExpenseInvalidError,
    ExpenseInvalidReason,
    ExpenseNotFoundError,
)
from app.domains.expenses.interactors.delete_expense import DeleteExpenseInteractor
from app.domains.expenses.interactors.dtos import (
    DeleteExpenseInputDTO,
    GetExpenseInputDTO,
    ListExpensesInputDTO,
    UpdateExpenseInputDTO,
)
from app.domains.expenses.interactors.get_expense import GetExpenseInteractor
from app.domains.expenses.interactors.list_expenses import ListExpensesInteractor
from app.domains.expenses.interactors.update_expense import UpdateExpenseInteractor
from app.domains.expenses.interfaces.dtos import (
    ExpenseCategory,
    ExpenseChanges,
    ExpenseDTO,
)
from app.domains.expenses.interfaces.repositories import ExpenseWrite
from tests.fakes.fake_expense_analytics_port import FakeExpenseAnalyticsPort
from tests.fakes.fake_expense_embed_queue import FakeExpenseEmbedQueue
from tests.fakes.fake_expense_repository import FakeExpenseRepository

USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()


async def _save(
    repository: FakeExpenseRepository,
    *,
    user_id: uuid.UUID = USER,
    amount_paise: int = 85_000,
    description: str = "dinner",
    category: ExpenseCategory = ExpenseCategory.FOOD,
    spent_on: date = date(2026, 10, 1),
) -> ExpenseDTO:
    return await repository.create_expense(
        user_id=user_id,
        write=ExpenseWrite(
            amount_paise=amount_paise,
            description=description,
            category=category,
            spent_on=spent_on,
            origin="command",
            original_input=f"/add-expense {description}",
        ),
    )


def _updater(
    repository: FakeExpenseRepository,
) -> tuple[UpdateExpenseInteractor, FakeExpenseAnalyticsPort]:
    analytics = FakeExpenseAnalyticsPort()
    return (
        UpdateExpenseInteractor(
            expense_repository=repository,
            analytics=analytics,
            embed_queue=FakeExpenseEmbedQueue(),
        ),
        analytics,
    )


async def _update(
    interactor: UpdateExpenseInteractor,
    expense: ExpenseDTO,
    changes: ExpenseChanges,
    *,
    user_id: uuid.UUID = USER,
) -> ExpenseDTO:
    return await interactor.update_expense(
        dto=UpdateExpenseInputDTO(
            user_id=user_id, expense_id=expense.id, changes=changes
        )
    )


async def test_the_list_filters_by_category_newest_spend_first() -> None:
    """C-14, FR-16, FR-17."""
    repository = FakeExpenseRepository()
    older = await _save(repository, spent_on=date(2026, 9, 28))
    newer = await _save(repository, spent_on=date(2026, 10, 1))
    await _save(repository, category=ExpenseCategory.TRANSPORT)
    interactor = ListExpensesInteractor(expense_repository=repository)

    food = await interactor.list_expenses(
        dto=ListExpensesInputDTO(
            user_id=USER, category=ExpenseCategory.FOOD, start=None, end=None
        )
    )

    assert food == [newer, older]


async def test_the_list_filters_by_an_inclusive_range() -> None:
    """Slice 2's period filter, which this signature already takes."""
    repository = FakeExpenseRepository()
    await _save(repository, spent_on=date(2026, 9, 30))
    first = await _save(repository, spent_on=date(2026, 10, 1))
    last = await _save(repository, spent_on=date(2026, 10, 31))
    interactor = ListExpensesInteractor(expense_repository=repository)

    october = await interactor.list_expenses(
        dto=ListExpensesInputDTO(
            user_id=USER,
            category=None,
            start=date(2026, 10, 1),
            end=date(2026, 10, 31),
        )
    )

    assert october == [last, first]


async def test_the_detail_is_not_found_for_another_user() -> None:
    """NFR-1: another user's expense reads as not found."""
    repository = FakeExpenseRepository()
    expense = await _save(repository)
    interactor = GetExpenseInteractor(expense_repository=repository)

    assert (
        await interactor.get_expense(
            dto=GetExpenseInputDTO(user_id=USER, expense_id=expense.id)
        )
        == expense
    )
    with pytest.raises(ExpenseNotFoundError):
        await interactor.get_expense(
            dto=GetExpenseInputDTO(user_id=OTHER_USER, expense_id=expense.id)
        )


async def test_each_field_changes_and_a_description_edit_keeps_the_category() -> None:
    """C-15, FR-21."""
    repository = FakeExpenseRepository()
    expense = await _save(repository)
    interactor, analytics = _updater(repository)

    updated = await _update(
        interactor, expense, ExpenseChanges(description="  team dinner ")
    )
    assert updated.description == "team dinner"
    assert updated.category == ExpenseCategory.FOOD
    assert repository.cleared_embeddings == [expense.id]

    updated = await _update(interactor, expense, ExpenseChanges(amount_paise=90_000))
    assert updated.amount_paise == 90_000

    updated = await _update(
        interactor, expense, ExpenseChanges(category=ExpenseCategory.ENTERTAINMENT)
    )
    assert updated.category == ExpenseCategory.ENTERTAINMENT

    assert analytics.events == ["expense_amount_edited", "expense_category_edited"]


async def test_only_a_description_edit_queues_a_new_vector() -> None:
    """Sub-plan 4.3: the old vector describes the old words, so the job runs
    again; an amount, category or date edit keeps the vector it has."""
    repository = FakeExpenseRepository()
    expense = await _save(repository)
    queue = FakeExpenseEmbedQueue()
    interactor = UpdateExpenseInteractor(
        expense_repository=repository,
        analytics=FakeExpenseAnalyticsPort(),
        embed_queue=queue,
    )

    await _update(interactor, expense, ExpenseChanges(amount_paise=90_000))
    await _update(interactor, expense, ExpenseChanges(description="dinner"))
    assert queue.queued == []

    await _update(interactor, expense, ExpenseChanges(description="team dinner"))
    assert queue.queued == [(USER, expense.id, 0)]


async def test_any_date_is_accepted_on_edit_including_the_future() -> None:
    """C-15, FR-21: no question on edit."""
    repository = FakeExpenseRepository()
    expense = await _save(repository)
    interactor, _ = _updater(repository)
    future = (datetime.now(UTC) + timedelta(days=400)).date()

    updated = await _update(interactor, expense, ExpenseChanges(spent_on=future))

    assert updated.spent_on == future


@pytest.mark.parametrize(
    ("changes", "field", "reason", "length"),
    [
        (
            ExpenseChanges(amount_paise=0),
            ExpenseField.AMOUNT,
            ExpenseInvalidReason.NOT_POSITIVE,
            None,
        ),
        (
            ExpenseChanges(amount_paise=-100),
            ExpenseField.AMOUNT,
            ExpenseInvalidReason.NOT_POSITIVE,
            None,
        ),
        (
            ExpenseChanges(description="   "),
            ExpenseField.DESCRIPTION,
            ExpenseInvalidReason.EMPTY,
            None,
        ),
        (
            ExpenseChanges(description="d" * 201),
            ExpenseField.DESCRIPTION,
            ExpenseInvalidReason.TOO_LONG,
            201,
        ),
    ],
)
async def test_an_invalid_edit_is_refused_and_changes_nothing(
    changes: ExpenseChanges,
    field: ExpenseField,
    reason: ExpenseInvalidReason,
    length: int | None,
) -> None:
    """C-15, FR-2, FR-13."""
    repository = FakeExpenseRepository()
    expense = await _save(repository)
    interactor, _ = _updater(repository)

    with pytest.raises(ExpenseInvalidError) as raised:
        await _update(interactor, expense, changes)

    assert (raised.value.field, raised.value.reason) == (field, reason)
    assert raised.value.length == length
    assert repository.rows[expense.id] == expense


async def test_editing_another_users_or_a_deleted_expense_is_not_found() -> None:
    repository = FakeExpenseRepository()
    expense = await _save(repository)
    interactor, _ = _updater(repository)

    with pytest.raises(ExpenseNotFoundError):
        await _update(
            interactor, expense, ExpenseChanges(amount_paise=1), user_id=OTHER_USER
        )
    repository.deleted.add(expense.id)
    with pytest.raises(ExpenseNotFoundError):
        await _update(interactor, expense, ExpenseChanges(amount_paise=1))


async def test_delete_removes_it_from_every_read_once() -> None:
    """C-16, FR-22."""
    repository = FakeExpenseRepository()
    expense = await _save(repository)
    analytics = FakeExpenseAnalyticsPort()
    interactor = DeleteExpenseInteractor(
        expense_repository=repository, analytics=analytics
    )

    await interactor.delete_expense(
        dto=DeleteExpenseInputDTO(user_id=USER, expense_id=expense.id)
    )

    assert expense.id in repository.deleted
    assert (
        await repository.list_for_user(
            user_id=USER, category=None, start=None, end=None
        )
        == []
    )
    assert await repository.get_by_id(user_id=USER, expense_id=expense.id) is None
    assert analytics.events == ["expense_deleted"]
    with pytest.raises(ExpenseNotFoundError):
        await interactor.delete_expense(
            dto=DeleteExpenseInputDTO(user_id=USER, expense_id=expense.id)
        )


async def test_another_user_cannot_delete_it() -> None:
    repository = FakeExpenseRepository()
    expense = await _save(repository)
    interactor = DeleteExpenseInteractor(
        expense_repository=repository, analytics=FakeExpenseAnalyticsPort()
    )

    with pytest.raises(ExpenseNotFoundError):
        await interactor.delete_expense(
            dto=DeleteExpenseInputDTO(user_id=OTHER_USER, expense_id=expense.id)
        )
    assert expense.id not in repository.deleted
