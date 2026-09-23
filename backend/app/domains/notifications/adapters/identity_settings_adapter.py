"""Implements notifications' DeliverySettingsPort and RecipientPort against the
identity domain."""

from uuid import UUID

from app.domains.identity.public import IdentityService
from app.domains.notifications.interfaces.dtos import DeliverySettings


class IdentityDeliverySettingsAdapter:
    def __init__(self, *, identity_service: IdentityService) -> None:
        self.identity_service = identity_service

    async def get_delivery_settings(self, *, user_id: UUID) -> DeliverySettings:
        settings = await self.identity_service.get_reminder_settings(user_id=user_id)
        return DeliverySettings(
            popups_enabled=settings.popups_enabled,
            email_enabled=settings.email_enabled,
            timezone=settings.timezone,
        )


class IdentityRecipientAdapter:
    def __init__(self, *, identity_service: IdentityService) -> None:
        self.identity_service = identity_service

    async def email_address(self, *, user_id: UUID) -> str | None:
        return await self.identity_service.get_account_email(user_id=user_id)
