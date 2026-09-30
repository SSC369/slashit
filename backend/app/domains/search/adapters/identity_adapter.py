"""Implements search's UserTimezonePort against the identity domain."""

from uuid import UUID

from app.domains.identity.public import IdentityService


class IdentityTimezoneAdapter:
    def __init__(self, *, identity_service: IdentityService) -> None:
        self.identity_service = identity_service

    async def get_user_timezone(self, *, user_id: UUID) -> str:
        settings = await self.identity_service.get_reminder_settings(user_id=user_id)
        return settings.timezone
