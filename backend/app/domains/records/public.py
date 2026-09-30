"""The only names other domains may import from records.

A domain's public surface is its contract. Adding a name here is a deliberate
act, reviewed like an API change. See backend/.claude/rules/repo-rules.md
section 6.
"""

from app.domains.records.interfaces.dtos import (
    Task,
    TaskDTO,
    TaskSearchMatchDTO,
    TaskSearchPageDTO,
    task_dto_to_type,
)
from app.domains.records.services.records_service import RecordsService

__all__ = [
    "RecordsService",
    "Task",
    "TaskDTO",
    "TaskSearchMatchDTO",
    "TaskSearchPageDTO",
    "task_dto_to_type",
]
