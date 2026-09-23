"""An in-memory SettingsRepository. Not a mock: it behaves, so tests read as
behaviour."""

from datetime import UTC, datetime
from uuid import UUID

from app.domains.identity.constants import (
    DEFAULT_EMAIL_ENABLED,
    DEFAULT_POPUPS_ENABLED,
    DEFAULT_REMINDER_TIME,
)
from app.domains.identity.interfaces.dtos import SettingsDTO


class FakeSettingsRepository:
    """Satisfies identity's SettingsRepository Protocol without inheriting from it."""

    def __init__(self) -> None:
        self.rows: dict[UUID, SettingsDTO] = {}

    async def get_for_user(self, *, user_id: UUID) -> SettingsDTO | None:
        return self.rows.get(user_id)

    async def upsert(self, *, user_id: UUID, timezone: str) -> SettingsDTO:
        now = datetime.now(UTC)
        existing = self.rows.get(user_id)
        settings = SettingsDTO(
            user_id=user_id,
            timezone=timezone,
            default_reminder_time=(
                existing.default_reminder_time if existing else DEFAULT_REMINDER_TIME
            ),
            popups_enabled=existing.popups_enabled
            if existing
            else DEFAULT_POPUPS_ENABLED,
            email_enabled=existing.email_enabled if existing else DEFAULT_EMAIL_ENABLED,
            channels_off_warned_at=existing.channels_off_warned_at
            if existing
            else None,
            created_at=existing.created_at if existing is not None else now,
            updated_at=now,
        )
        self.rows[user_id] = settings
        return settings
