"""FR-31 to FR-34: the default reminder time and the two delivery switches."""

from collections.abc import Callable
from datetime import datetime, time

from app.domains.identity.constants import (
    DEFAULT_EMAIL_ENABLED,
    DEFAULT_POPUPS_ENABLED,
    DEFAULT_REMINDER_TIME,
    DEFAULT_TIMEZONE,
)
from app.domains.identity.graphql.errors import InvalidReminderSettingsError
from app.domains.identity.interactors.dtos import UpdateReminderSettingsInputDTO
from app.domains.identity.interfaces.dtos import ReminderSettingsSavedDTO, SettingsDTO
from app.domains.identity.interfaces.repositories import (
    ReminderSettingsWrite,
    SettingsRepository,
)


class UpdateReminderSettingsInteractor:
    def __init__(
        self,
        *,
        settings_repository: SettingsRepository,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.settings_repository = settings_repository
        self.now_provider = now_provider

    async def update_reminder_settings(
        self, *, dto: UpdateReminderSettingsInputDTO
    ) -> ReminderSettingsSavedDTO:
        """Save what changed. The first save that leaves both switches off
        says so once (FR-34), and never again for that user.

        Raises:
            InvalidReminderSettingsError: the default time is not "HH:MM".
        """
        default_time = self._validate_default_time(raw_time=dto.default_reminder_time)
        current = await self.settings_repository.get_for_user(user_id=dto.user_id)
        write = self._merge(current=current, dto=dto, default_time=default_time)
        should_warn = self._is_first_time_both_off(current=current, write=write)
        if should_warn:
            write = ReminderSettingsWrite(
                default_reminder_time=write.default_reminder_time,
                popups_enabled=write.popups_enabled,
                email_enabled=write.email_enabled,
                channels_off_warned_at=self.now_provider(),
            )
        saved = await self.settings_repository.save_reminder_settings(
            user_id=dto.user_id, write=write, timezone_if_new=DEFAULT_TIMEZONE
        )
        return ReminderSettingsSavedDTO(
            settings=saved, show_both_off_warning=should_warn
        )

    def _validate_default_time(self, *, raw_time: str | None) -> time | None:
        if raw_time is None:
            return None
        try:
            parsed = time.fromisoformat(raw_time)
        except ValueError as error:
            raise InvalidReminderSettingsError(
                field="defaultReminderTime", message="Pick a time."
            ) from error
        return parsed.replace(second=0, microsecond=0)

    def _merge(
        self,
        *,
        current: SettingsDTO | None,
        dto: UpdateReminderSettingsInputDTO,
        default_time: time | None,
    ) -> ReminderSettingsWrite:
        stored_time = (
            current.default_reminder_time if current else DEFAULT_REMINDER_TIME
        )
        return ReminderSettingsWrite(
            default_reminder_time=default_time
            if default_time is not None
            else stored_time,
            popups_enabled=_first_set(
                chosen=dto.popups_enabled,
                fallback=current.popups_enabled if current else DEFAULT_POPUPS_ENABLED,
            ),
            email_enabled=_first_set(
                chosen=dto.email_enabled,
                fallback=current.email_enabled if current else DEFAULT_EMAIL_ENABLED,
            ),
            channels_off_warned_at=current.channels_off_warned_at if current else None,
        )

    def _is_first_time_both_off(
        self, *, current: SettingsDTO | None, write: ReminderSettingsWrite
    ) -> bool:
        is_both_off = not write.popups_enabled and not write.email_enabled
        was_warned = current is not None and current.channels_off_warned_at is not None
        return is_both_off and not was_warned


def _first_set(*, chosen: bool | None, fallback: bool) -> bool:
    return fallback if chosen is None else chosen
