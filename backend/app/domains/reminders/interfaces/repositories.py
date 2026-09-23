"""The contract for reminder storage. Storage reads and writes; it never decides."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.reminders.interfaces.dtos import (
    RecordOriginValue,
    ReminderDTO,
    ReminderStateValue,
)
from app.domains.reminders.services.schedule import ScheduleSpec


@dataclass(frozen=True)
class ReminderWrite:
    """Everything a create or a series edit stores. Built by an interactor."""

    description: str
    spec: ScheduleSpec
    schedule_timezone: str
    next_fire_at: datetime | None
    state: ReminderStateValue


class ReminderRepository(Protocol):
    async def create_reminder(
        self,
        *,
        user_id: UUID,
        write: ReminderWrite,
        origin: RecordOriginValue,
        original_input: str | None,
    ) -> ReminderDTO: ...

    async def count_active_for_user(self, *, user_id: UUID) -> int:
        """Live and not done. The 100-reminder cap reads this (FR-38)."""
        ...

    async def list_for_user(
        self, *, user_id: UUID, search: str | None
    ) -> list[ReminderDTO]:
        """Every live reminder, unordered. Grouping is the interactor's."""
        ...

    async def get_by_id(
        self, *, user_id: UUID, reminder_id: UUID
    ) -> ReminderDTO | None:
        """A live reminder the user owns, or None."""
        ...

    async def is_deleted(self, *, user_id: UUID, reminder_id: UUID) -> bool:
        """Whether the user owns this id and it was deleted. Lets an edit tell
        "deleted meanwhile" from "never yours" (ReminderEditGone)."""
        ...

    async def update_series(
        self, *, user_id: UUID, reminder_id: UUID, write: ReminderWrite
    ) -> ReminderDTO | None: ...

    async def soft_delete(self, *, user_id: UUID, reminder_id: UUID) -> bool:
        """Sets ``deleted_at`` and clears ``next_fire_at``. False if not found."""
        ...
