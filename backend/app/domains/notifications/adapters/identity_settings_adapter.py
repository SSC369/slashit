"""Implements notifications' DeliverySettingsPort against the identity domain."""

from uuid import UUID

from app.domains.identity.public import IdentityService


class IdentityDeliverySettingsAdapter:
    def __init__(self, *, identity_service: IdentityService) -> None:
        self.identity_service = identity_service

    async def popups_enabled(self, *, user_id: UUID) -> bool:
        settings = await self.identity_service.get_reminder_settings(user_id=user_id)
        return settings.popups_enabled
