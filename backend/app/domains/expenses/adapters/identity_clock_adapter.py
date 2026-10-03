"""Implements expenses' LocalDatePort against the identity domain (AD-3).
Closes dev log D-5."""

from datetime import UTC, date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domains.identity.public import IdentityService


class IdentityLocalDateAdapter:
    def __init__(self, *, identity_service: IdentityService) -> None:
        self.identity_service = identity_service

    async def local_today(self, *, user_id: UUID) -> date:
        settings = await self.identity_service.get_reminder_settings(user_id=user_id)
        return datetime.now(UTC).astimezone(ZoneInfo(settings.timezone)).date()
