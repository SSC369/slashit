from dataclasses import dataclass
from datetime import datetime, time
from typing import Protocol
from uuid import UUID

from app.domains.identity.interfaces.dtos import (
    AuthAttemptOutcomeDTO,
    ProfileDTO,
    SettingsDTO,
)


@dataclass(frozen=True)
class ReminderSettingsWrite:
    """The reminder settings a save writes, whole. The interactor carries
    forward what the caller did not change."""

    default_reminder_time: time
    popups_enabled: bool
    email_enabled: bool
    channels_off_warned_at: datetime | None


class SettingsRepository(Protocol):
    async def get_for_user(self, *, user_id: UUID) -> SettingsDTO | None: ...

    async def upsert(self, *, user_id: UUID, timezone: str) -> SettingsDTO: ...

    async def save_reminder_settings(
        self, *, user_id: UUID, write: ReminderSettingsWrite, timezone_if_new: str
    ) -> SettingsDTO:
        """Writes the reminder columns; creates the row, with
        ``timezone_if_new``, if the user has none yet."""
        ...


class ProfileRepository(Protocol):
    async def get_for_user(self, *, user_id: UUID) -> ProfileDTO | None: ...


class AuthAccountRepository(Protocol):
    """Reaches ``auth.users`` directly, on the service-role connection only.

    Never scoped to one user: this is what the background sweep in
    ``jobs.py`` runs against, per rule T3. No other repository in this
    codebase talks to ``auth.users`` for writes.
    """

    async def delete_unverified_created_before(self, *, cutoff: datetime) -> int: ...

    async def get_email(self, *, user_id: UUID) -> str | None:
        """The account's address, for reminder email (epic 003 FR-14). Read
        on the service-role connection by the email job only."""
        ...


class AuthAttemptRepository(Protocol):
    """FR-17's sign-in lockout, moved into the app (2026-09-19: the Password
    Verification Attempt hook is Teams/Enterprise only)."""

    async def is_locked(self, *, email: str) -> AuthAttemptOutcomeDTO:
        """Read-only: the current lock state, no side effect."""
        ...

    async def record_attempt(self, *, email: str, valid: bool) -> AuthAttemptOutcomeDTO:
        """Count one attempt and return the resulting lock state."""
        ...
