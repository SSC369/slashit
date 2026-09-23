"""Identity's published surface for other domains, index §4.

Reminders reads a user's clock through this in slice 1; notifications will read
the channel switches and the account email from slice 2 on. Nothing here
writes.
"""

from uuid import UUID

from app.domains.identity.constants import (
    DEFAULT_EMAIL_ENABLED,
    DEFAULT_POPUPS_ENABLED,
    DEFAULT_REMINDER_TIME,
    DEFAULT_TIMEZONE,
)
from app.domains.identity.interfaces.dtos import ReminderSettingsDTO
from app.domains.identity.interfaces.repositories import SettingsRepository


class IdentityService:
    def __init__(self, *, settings_repository: SettingsRepository) -> None:
        self.settings_repository = settings_repository

    async def get_reminder_settings(self, *, user_id: UUID) -> ReminderSettingsDTO:
        """The user's settings, or the defaults if they have no row yet.

        No row is rare: the app creates one on first load (001 FR-28). This
        read never creates one, so a background job can call it safely.
        """
        settings = await self.settings_repository.get_for_user(user_id=user_id)
        if settings is None:
            return ReminderSettingsDTO(
                timezone=DEFAULT_TIMEZONE,
                default_reminder_time=DEFAULT_REMINDER_TIME,
                popups_enabled=DEFAULT_POPUPS_ENABLED,
                email_enabled=DEFAULT_EMAIL_ENABLED,
                channels_off_warned_at=None,
            )
        return ReminderSettingsDTO(
            timezone=settings.timezone,
            default_reminder_time=settings.default_reminder_time,
            popups_enabled=settings.popups_enabled,
            email_enabled=settings.email_enabled,
            channels_off_warned_at=settings.channels_off_warned_at,
        )
