"""Implements reminders' UserClockPort against the identity domain."""

from uuid import UUID

from app.domains.identity.public import IdentityService
from app.domains.reminders.interfaces.dtos import UserClockDTO


class IdentityUserClockAdapter:
    def __init__(self, *, identity_service: IdentityService) -> None:
        self.identity_service = identity_service

    async def get_user_clock(self, *, user_id: UUID) -> UserClockDTO:
        settings = await self.identity_service.get_reminder_settings(user_id=user_id)
        return UserClockDTO(
            timezone=settings.timezone,
            default_reminder_time=settings.default_reminder_time,
        )
