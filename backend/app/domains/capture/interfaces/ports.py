"""What capture needs from other domains, in its own words.

Per repo-rules.md section 6, the port belongs to the consumer. Neither
Protocol names ``records`` or ``gateway``; each names the one thing capture
needs, in capture's vocabulary.
"""

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from app.domains.gateway.public import ExtractionResult
from app.domains.records.public import TaskDTO


class TaskPort(Protocol):
    """What capture needs from records: create one task, list a user's open
    ones for `/tasks`. Named for what it does, not for the domain it reaches.
    """

    async def create_task(
        self,
        *,
        user_id: UUID,
        title: str,
        due_at: datetime | None,
        original_input: str,
    ) -> TaskDTO: ...

    async def list_open_tasks(self, *, user_id: UUID) -> list[TaskDTO]: ...


class ExtractionPort(Protocol):
    async def extract(
        self,
        *,
        user_id: UUID,
        prompt: str,
        schema: dict[str, Any],
        instruction: str,
    ) -> ExtractionResult: ...


class AnalyticsPort(Protocol):
    """What capture needs from analytics: log a no-command session. FR-9's
    metric (PRD section 8) has no other data source."""

    async def record_no_command_input(self, *, user_id: UUID) -> None: ...
