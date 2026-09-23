"""Backs the `records` query. See 04.2-records-and-settings.md.

Epic 003 (sub-plan 4.1) adds reminders: with no kind filter, the All tab
merges both record types into one list, ordered by the requested field.
"""

from datetime import UTC, datetime

from app.domains.records.interactors.dtos import ListTasksInputDTO
from app.domains.records.interfaces.dtos import TaskDTO
from app.domains.records.interfaces.ports import ReminderRecordsPort
from app.domains.records.interfaces.repositories import TaskRepository
from app.domains.reminders.public import ReminderDTO

RecordItemDTO = TaskDTO | ReminderDTO

_TASKS_ONLY = "TASKS"
_REMINDERS_ONLY = "REMINDERS"
_DUE_AT = "DUE_AT"
# A record with no date sorts after every dated one, as the tasks query does.
_UNDATED = datetime.max.replace(tzinfo=UTC)


class ListTasksInteractor:
    def __init__(
        self,
        *,
        task_repository: TaskRepository,
        reminder_records: ReminderRecordsPort,
    ) -> None:
        self.task_repository = task_repository
        self.reminder_records = reminder_records

    async def list_tasks(self, *, dto: ListTasksInputDTO) -> list[RecordItemDTO]:
        """List the caller's records, filtered, searched and sorted."""
        tasks: list[TaskDTO] = []
        reminders: list[ReminderDTO] = []
        if dto.kind_filter != _REMINDERS_ONLY:
            tasks = await self.task_repository.list_for_user(
                user_id=dto.user_id,
                kind_filter=dto.kind_filter,
                search=dto.search,
                sort_by=dto.sort_by,
                sort_desc=dto.sort_desc,
            )
        if dto.kind_filter != _TASKS_ONLY:
            reminders = await self.reminder_records.list_reminders(
                user_id=dto.user_id, search=dto.search
            )
        if not reminders:
            return list(tasks)
        return self._merge_in_order(tasks=tasks, reminders=reminders, dto=dto)

    def _merge_in_order(
        self,
        *,
        tasks: list[TaskDTO],
        reminders: list[ReminderDTO],
        dto: ListTasksInputDTO,
    ) -> list[RecordItemDTO]:
        merged: list[RecordItemDTO] = [*tasks, *reminders]
        dated = [
            item for item in merged if self._sort_key(item=item, dto=dto) is not None
        ]
        undated = [
            item for item in merged if self._sort_key(item=item, dto=dto) is None
        ]
        dated.sort(
            key=lambda item: self._sort_key(item=item, dto=dto) or _UNDATED,
            reverse=dto.sort_desc,
        )
        return [*dated, *undated]

    def _sort_key(
        self, *, item: RecordItemDTO, dto: ListTasksInputDTO
    ) -> datetime | None:
        if dto.sort_by != _DUE_AT:
            return item.created_at
        if isinstance(item, TaskDTO):
            return item.due_at
        return item.next_fire_at
