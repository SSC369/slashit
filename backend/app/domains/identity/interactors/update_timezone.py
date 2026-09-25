from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domains.identity.graphql.errors import InvalidTimezoneError
from app.domains.identity.interactors.dtos import UpdateTimezoneInputDTO
from app.domains.identity.interfaces.dtos import SettingsDTO
from app.domains.identity.interfaces.ports import TimezoneChangeQueuePort
from app.domains.identity.interfaces.repositories import SettingsRepository


class UpdateTimezoneInteractor:
    def __init__(
        self,
        *,
        settings_repository: SettingsRepository,
        timezone_change_queue: TimezoneChangeQueuePort,
    ) -> None:
        self.settings_repository = settings_repository
        self.timezone_change_queue = timezone_change_queue

    async def update_timezone(self, *, dto: UpdateTimezoneInputDTO) -> SettingsDTO:
        """Change the caller's stored timezone, then announce the change so
        reminders can move (003 FR-10, FR-11).

        Raises:
            InvalidTimezoneError: the string is not a real IANA zone.
        """
        self._validate_timezone(timezone=dto.timezone)
        previous = await self.settings_repository.get_for_user(user_id=dto.user_id)
        saved = await self.settings_repository.upsert(
            user_id=dto.user_id, timezone=dto.timezone
        )
        if previous is None or previous.timezone != saved.timezone:
            await self.timezone_change_queue.enqueue_timezone_change(
                user_id=dto.user_id
            )
        return saved

    def _validate_timezone(self, *, timezone: str) -> None:
        try:
            ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise InvalidTimezoneError(timezone=timezone) from error
