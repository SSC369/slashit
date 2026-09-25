"""The reminders domain's published surface, index §4.

Other domains reach reminders only through this class, re-exported from
``public.py`` and called through their own port and adapter (repo-rules.md
section 6). Creating delegates to the one use case that owns the rules.
"""

from datetime import UTC, datetime
from uuid import UUID

from app.domains.reminders.interactors.create_reminder import (
    CreateReminderInteractor,
    CreateReminderOutcome,
)
from app.domains.reminders.interfaces.dtos import (
    RecordOriginValue,
    ReminderDTO,
    ReminderFields,
)
from app.domains.reminders.interfaces.repositories import ReminderRepository

_FAR_FUTURE = datetime.max.replace(tzinfo=UTC)


class ReminderService:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        create_reminder_interactor: CreateReminderInteractor,
    ) -> None:
        self.reminder_repository = reminder_repository
        self.create_reminder_interactor = create_reminder_interactor

    async def create_reminder(
        self,
        *,
        user_id: UUID,
        fields: ReminderFields,
        origin: RecordOriginValue,
        original_input: str | None,
    ) -> CreateReminderOutcome:
        return await self.create_reminder_interactor.create_reminder(
            user_id=user_id, fields=fields, origin=origin, original_input=original_input
        )

    async def list_active(self, *, user_id: UUID) -> list[ReminderDTO]:
        """FR-25, `/reminders`: live and not done. A fired one-time reminder has
        no next time and sorts first, since it needs attention."""
        reminders = await self.reminder_repository.list_for_user(
            user_id=user_id, search=None
        )
        active = [item for item in reminders if item.state != "done"]
        return sorted(
            active,
            key=lambda item: (item.state != "fired", item.next_due_at or _FAR_FUTURE),
        )

    async def list_for_records(
        self, *, user_id: UUID, search: str | None
    ) -> list[ReminderDTO]:
        """Every live reminder, for the Records All tab. Records orders them."""
        return await self.reminder_repository.list_for_user(
            user_id=user_id, search=search
        )
