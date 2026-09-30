"""Implements records' ReminderRecordsPort against the reminders domain."""

from uuid import UUID

from app.domains.reminders.public import ReminderDTO, ReminderService


class ReminderRecordsAdapter:
    def __init__(self, *, reminder_service: ReminderService) -> None:
        self.reminder_service = reminder_service

    async def list_reminders(self, *, user_id: UUID) -> list[ReminderDTO]:
        # Epic 005, FR-22: the records view never lists by text any more.
        return await self.reminder_service.list_for_records(
            user_id=user_id, search=None
        )
