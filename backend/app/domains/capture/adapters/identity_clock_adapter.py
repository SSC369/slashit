"""Implements capture's LocalClockPort against the identity domain (AD-7)."""

from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domains.identity.public import IdentityService


class IdentityLocalClockAdapter:
    def __init__(self, *, identity_service: IdentityService) -> None:
        self.identity_service = identity_service

    async def local_now(self, *, user_id: UUID) -> tuple[datetime, str]:
        settings = await self.identity_service.get_reminder_settings(user_id=user_id)
        return datetime.now(UTC).astimezone(
            ZoneInfo(settings.timezone)
        ), settings.timezone
