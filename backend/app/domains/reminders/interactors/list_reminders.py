"""FR-26: the Reminders tab, grouped Needs attention, Upcoming, Done."""

from datetime import UTC, datetime

from app.domains.reminders.interactors.dtos import ListRemindersInputDTO
from app.domains.reminders.interfaces.dtos import ReminderDTO, ReminderGroupsDTO
from app.domains.reminders.interfaces.repositories import ReminderRepository

# Sorts a reminder with no next fire time after every one that has one.
_FAR_FUTURE = datetime.max.replace(tzinfo=UTC)


class ListRemindersInteractor:
    def __init__(self, *, reminder_repository: ReminderRepository) -> None:
        self.reminder_repository = reminder_repository

    async def list_reminders(self, *, dto: ListRemindersInputDTO) -> ReminderGroupsDTO:
        """Group the caller's live reminders. Fired ones need attention, newest
        first; upcoming ones soonest first; done ones most recent first."""
        reminders = await self.reminder_repository.list_for_user(
            user_id=dto.user_id, search=dto.search
        )
        return ReminderGroupsDTO(
            needs_attention=self._newest_first(
                reminders=[item for item in reminders if item.state == "fired"]
            ),
            upcoming=self._soonest_first(
                reminders=[item for item in reminders if item.state == "upcoming"]
            ),
            done=self._newest_first(
                reminders=[item for item in reminders if item.state == "done"]
            ),
        )

    def _soonest_first(self, *, reminders: list[ReminderDTO]) -> list[ReminderDTO]:
        return sorted(reminders, key=lambda item: item.next_fire_at or _FAR_FUTURE)

    def _newest_first(self, *, reminders: list[ReminderDTO]) -> list[ReminderDTO]:
        return sorted(
            reminders,
            key=lambda item: item.last_fired_at or item.updated_at,
            reverse=True,
        )
