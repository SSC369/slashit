"""FR-27: one reminder's detail."""

from app.domains.reminders.graphql.errors import ReminderNotFoundError
from app.domains.reminders.interactors.dtos import GetReminderInputDTO
from app.domains.reminders.interfaces.dtos import ReminderDTO
from app.domains.reminders.interfaces.repositories import ReminderRepository


class GetReminderInteractor:
    def __init__(self, *, reminder_repository: ReminderRepository) -> None:
        self.reminder_repository = reminder_repository

    async def get_reminder(self, *, dto: GetReminderInputDTO) -> ReminderDTO:
        """Return one live reminder the caller owns.

        Raises:
            ReminderNotFoundError: no live reminder with this id is theirs.
                Deleted and another user's read the same (NFR-6).
        """
        reminder = await self.reminder_repository.get_by_id(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        )
        if reminder is None:
            raise ReminderNotFoundError()
        return reminder
