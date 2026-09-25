"""Backs the `records` query. See 04.2-records-and-settings.md.

Epic 003 (sub-plan 4.1) adds reminders: with no kind filter, the All tab
merges both record types into one list, ordered by the requested field. Epic
004 (sub-plan 4.1) adds memories the same way; a memory has no due date, so it
sorts with the undated records when sorting by due date.
"""

from datetime import UTC, datetime

from app.domains.memories.public import MemoryDTO
from app.domains.records.interactors.dtos import ListTasksInputDTO
from app.domains.records.interfaces.dtos import TaskDTO
from app.domains.records.interfaces.ports import MemoryRecordsPort, ReminderRecordsPort
from app.domains.records.interfaces.repositories import TaskRepository
from app.domains.reminders.public import ReminderDTO

RecordItemDTO = TaskDTO | ReminderDTO | MemoryDTO

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
        memory_records: MemoryRecordsPort,
    ) -> None:
        self.task_repository = task_repository
        self.reminder_records = reminder_records
        self.memory_records = memory_records

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
        memories: list[MemoryDTO] = []
        if dto.kind_filter is None:
            memories = await self.memory_records.list_memories(
                user_id=dto.user_id, search=dto.search
            )
        if not reminders and not memories:
            return list(tasks)
        return self._merge_in_order(records=[*tasks, *reminders, *memories], dto=dto)

    def _merge_in_order(
        self, *, records: list[RecordItemDTO], dto: ListTasksInputDTO
    ) -> list[RecordItemDTO]:
        merged = records
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
        if isinstance(item, MemoryDTO):
            return None
        return item.next_fire_at
