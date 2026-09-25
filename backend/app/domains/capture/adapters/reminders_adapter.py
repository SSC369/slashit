"""Implements capture's ReminderPort against the reminders domain."""

from uuid import UUID

from app.domains.reminders.public import (
    ReminderDTO,
    ReminderFields,
    ReminderLimitReached,
    ReminderNeedsWhen,
    ReminderService,
)


class RemindersAdapter:
    def __init__(self, *, reminder_service: ReminderService) -> None:
        self.reminder_service = reminder_service

    async def create_reminder(
        self, *, user_id: UUID, fields: ReminderFields, original_input: str
    ) -> ReminderDTO | ReminderLimitReached | ReminderNeedsWhen:
        return await self.reminder_service.create_reminder(
            user_id=user_id,
            fields=fields,
            origin="command",
            original_input=original_input,
        )

    async def list_active(self, *, user_id: UUID) -> list[ReminderDTO]:
        return await self.reminder_service.list_active(user_id=user_id)
