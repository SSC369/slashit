from datetime import datetime

import strawberry

from app.domains.records.graphql.types import SortField, TaskStatus


@strawberry.input
class RecordsFilterInput:
    kind: str | None = None
    # Epic 005, FR-22: no `search`. The records view calls search's own
    # `search` query whenever the box holds text.
    sort_by: SortField = SortField.CREATED_AT
    sort_desc: bool = False


@strawberry.input
class UpdateTaskInput:
    title: str | None = None
    status: TaskStatus | None = None
    # UNSET (omitted) means "leave due_at as it is"; an explicit null means
    # "clear it". title/status don't need this distinction: a task's title
    # is never legitimately blank and its status is never legitimately
    # absent, but a due date is legitimately absent (FR-23).
    due_at: datetime | None = strawberry.UNSET
