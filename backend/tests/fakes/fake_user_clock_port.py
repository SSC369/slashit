"""An in-memory UserClockPort for reminders: a fixed zone and default time."""

from datetime import time
from uuid import UUID

from app.domains.reminders.interfaces.dtos import UserClockDTO


class FakeUserClockPort:
    def __init__(
        self, *, timezone: str = "Asia/Kolkata", default_reminder_time: time = time(9)
    ) -> None:
        self.clock = UserClockDTO(
            timezone=timezone, default_reminder_time=default_reminder_time
        )

    async def get_user_clock(self, *, user_id: UUID) -> UserClockDTO:
        return self.clock
