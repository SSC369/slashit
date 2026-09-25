"""The only SQL in the identity domain. Returns DTOs, never models."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.identity.interfaces.dtos import SettingsDTO
from app.domains.identity.interfaces.repositories import ReminderSettingsWrite
from app.domains.identity.models import UserSettings


class SqlSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_user(self, *, user_id: UUID) -> SettingsDTO | None:
        async with user_transaction(self.session, user_id) as scoped:
            settings = await scoped.get(UserSettings, user_id)
        if settings is None:
            return None
        return _settings_to_dto(settings=settings)

    async def upsert(self, *, user_id: UUID, timezone: str) -> SettingsDTO:
        now = datetime.now(UTC)
        async with user_transaction(self.session, user_id) as scoped:
            statement = insert(UserSettings).values(
                user_id=user_id, timezone=timezone, created_at=now, updated_at=now
            )
            statement = statement.on_conflict_do_update(
                index_elements=[UserSettings.user_id],
                set_={"timezone": timezone, "updated_at": now},
            )
            await scoped.execute(statement)
            settings = await scoped.get(UserSettings, user_id)
        if settings is None:  # pragma: no cover — the upsert above guarantees this
            raise RuntimeError("Upsert did not produce a row")
        return _settings_to_dto(settings=settings)

    async def save_reminder_settings(
        self, *, user_id: UUID, write: ReminderSettingsWrite, timezone_if_new: str
    ) -> SettingsDTO:
        now = datetime.now(UTC)
        columns = {
            "default_reminder_time": write.default_reminder_time,
            "popups_enabled": write.popups_enabled,
            "email_enabled": write.email_enabled,
            "channels_off_warned_at": write.channels_off_warned_at,
        }
        async with user_transaction(self.session, user_id) as scoped:
            statement = insert(UserSettings).values(
                user_id=user_id,
                timezone=timezone_if_new,
                created_at=now,
                updated_at=now,
                **columns,
            )
            statement = statement.on_conflict_do_update(
                index_elements=[UserSettings.user_id],
                set_={**columns, "updated_at": now},
            )
            await scoped.execute(statement)
            settings = await scoped.get(UserSettings, user_id, populate_existing=True)
        if settings is None:  # pragma: no cover — the upsert above guarantees this
            raise RuntimeError("Upsert did not produce a row")
        return _settings_to_dto(settings=settings)


def _settings_to_dto(*, settings: UserSettings) -> SettingsDTO:
    return SettingsDTO(
        user_id=settings.user_id,
        timezone=settings.timezone,
        default_reminder_time=settings.default_reminder_time,
        popups_enabled=settings.popups_enabled,
        email_enabled=settings.email_enabled,
        channels_off_warned_at=settings.channels_off_warned_at,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )
