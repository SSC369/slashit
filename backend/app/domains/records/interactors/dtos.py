"""Input DTOs for the records interactors. One per use case, per code-rules.md."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domains.records.interfaces.dtos import TaskStatus


@dataclass(frozen=True)
class ListTasksInputDTO:
    user_id: UUID
    kind_filter: str | None
    sort_by: str
    sort_desc: bool


@dataclass(frozen=True)
class GetRecordDetailInputDTO:
    user_id: UUID
    task_id: UUID


@dataclass(frozen=True)
class UpdateTaskInputDTO:
    user_id: UUID
    task_id: UUID
    title: str | None
    status: TaskStatus | None
    due_at: datetime | None
    due_at_provided: bool


@dataclass(frozen=True)
class DeleteTasksInputDTO:
    user_id: UUID
    task_ids: list[UUID]


@dataclass(frozen=True)
class EmbedTaskInputDTO:
    user_id: UUID
    task_id: UUID


@dataclass(frozen=True)
class QueueMissingTaskEmbeddingsInputDTO:
    """``full`` sweeps every task with no vector, once at deploy (005 FR-13);
    otherwise only tasks touched in the backfill window."""

    full: bool
