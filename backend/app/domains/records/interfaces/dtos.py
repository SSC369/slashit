"""Data crossing the records domain's boundaries. Frozen, never a model instance."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

import strawberry

TaskStatus = Literal["pending", "done"]
RecordOrigin = Literal["command", "edit"]


@dataclass(frozen=True)
class TaskDTO:
    """One task, as every layer above the repository sees it."""

    id: UUID
    user_id: UUID
    title: str
    due_at: datetime | None
    status: TaskStatus
    is_overdue: bool
    origin: RecordOrigin
    original_input: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TaskSearchMatchDTO:
    """One task a search matched, with the scores search ranks by (005 AD-3).

    ``word_rank`` is None when no term is present; ``distance`` is None when
    the task has no vector yet or the search had none.
    """

    task: TaskDTO
    all_terms: bool
    word_rank: float | None
    distance: float | None


@dataclass(frozen=True)
class TaskSearchPageDTO:
    matches: list[TaskSearchMatchDTO]
    total: int


@dataclass(frozen=True)
class TaskEmbeddingTargetDTO:
    """A task the embed backfill should queue: owner, id, nothing readable."""

    user_id: UUID
    task_id: UUID


@strawberry.type
class Task:
    """The crossable GraphQL shape.

    Lives here, in ``interfaces/``, not under ``graphql/``, so it may cross a
    domain boundary per repo-rules.md section 6.2 — the same placement the
    gateway uses for ``Extraction`` in its own ``errors.py``.
    """

    id: strawberry.ID
    title: str
    due_at: datetime | None
    status: str
    is_overdue: bool
    origin: str
    original_input: str | None
    created_at: datetime
    updated_at: datetime


def task_dto_to_type(*, task: TaskDTO) -> Task:
    return Task(
        id=strawberry.ID(str(task.id)),
        title=task.title,
        due_at=task.due_at,
        status=task.status,
        is_overdue=task.is_overdue,
        origin=task.origin,
        original_input=task.original_input,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
