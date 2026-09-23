"""An in-memory ReminderRecordsPort for records' All tab."""

from uuid import UUID

from app.domains.reminders.public import ReminderDTO


class FakeReminderRecordsPort:
    def __init__(self, *, reminders: list[ReminderDTO] | None = None) -> None:
        self.reminders = list(reminders or [])

    async def list_reminders(
        self, *, user_id: UUID, search: str | None
    ) -> list[ReminderDTO]:
        return [
            reminder
            for reminder in self.reminders
            if reminder.user_id == user_id
            and (not search or search.lower() in reminder.description.lower())
        ]
