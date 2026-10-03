"""FR-16: how a ranked record is described to the model. Pure.

Type, its words, and the one or two facts a question about it needs. Never an
id: the model refers to a record only by its number (build plan §5).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.domains.expenses.public import ExpenseDTO
from app.domains.memories.public import MemoryDTO
from app.domains.records.public import TaskDTO
from app.domains.reminders.public import ReminderDTO
from app.domains.search.interfaces.dtos import AnswerRecordDTO, RecordDTO, RecordType

_DATE_FORMAT = "%a %d %b %Y"


def describe_record(
    *, number: int, record_type: RecordType, item: RecordDTO, timezone: ZoneInfo
) -> AnswerRecordDTO:
    if isinstance(item, TaskDTO):
        due = (
            f"due {_local_date(moment=item.due_at, timezone=timezone)}"
            if item.due_at is not None
            else "no due date"
        )
        return AnswerRecordDTO(
            number=number,
            record_type=record_type,
            text=item.title,
            detail=f"task, {due}, {item.status}",
        )
    if isinstance(item, ReminderDTO):
        return AnswerRecordDTO(
            number=number,
            record_type=record_type,
            text=item.description,
            detail=f"reminder, {item.summary.when_text}, {item.state}",
        )
    if isinstance(item, ExpenseDTO):
        return _describe_expense(number=number, expense=item)
    return _describe_memory(number=number, memory=item, timezone=timezone)


def _describe_expense(*, number: int, expense: ExpenseDTO) -> AnswerRecordDTO:
    """006 sub-plan 4.3: amount, day and category, so "how much did I spend
    on uber" can be answered from the records alone."""
    rupees, paise = divmod(expense.amount_paise, 100)
    amount = f"₹{rupees}" if paise == 0 else f"₹{rupees}.{paise:02d}"
    spent_on = expense.spent_on.strftime(_DATE_FORMAT)
    return AnswerRecordDTO(
        number=number,
        record_type=RecordType.EXPENSE,
        text=expense.description,
        detail=f"expense, {amount} on {spent_on}, {expense.category.value}",
    )


def _describe_memory(
    *, number: int, memory: MemoryDTO, timezone: ZoneInfo
) -> AnswerRecordDTO:
    saved = _local_date(moment=memory.created_at, timezone=timezone)
    return AnswerRecordDTO(
        number=number,
        record_type=RecordType.MEMORY,
        text=memory.text,
        detail=f"memory, saved {saved}",
    )


def _local_date(*, moment: datetime, timezone: ZoneInfo) -> str:
    return moment.astimezone(timezone).strftime(_DATE_FORMAT)
