"""An in-memory AuthAttemptRepository. Not a mock: it behaves, so tests read
as behaviour. Mirrors SqlAuthAttemptRepository's counting logic exactly."""

from datetime import UTC, datetime

from app.domains.identity.constants import (
    SIGN_IN_ATTEMPT_WINDOW,
    SIGN_IN_LOCKOUT_DURATION,
    SIGN_IN_MAX_FAILED_ATTEMPTS,
)
from app.domains.identity.interfaces.dtos import AuthAttemptOutcomeDTO

_NOT_LOCKED = AuthAttemptOutcomeDTO(locked=False, locked_until=None)


class _Row:
    def __init__(self, *, now: datetime) -> None:
        self.failed_count = 0
        self.window_started_at = now
        self.locked_until: datetime | None = None


class FakeAuthAttemptRepository:
    def __init__(self) -> None:
        self.rows: dict[str, _Row] = {}

    async def is_locked(self, *, email: str) -> AuthAttemptOutcomeDTO:
        row = self.rows.get(email)
        now = datetime.now(UTC)
        if row is None or row.locked_until is None or row.locked_until <= now:
            return _NOT_LOCKED
        return AuthAttemptOutcomeDTO(locked=True, locked_until=row.locked_until)

    async def record_attempt(
        self, *, email: str, valid: bool
    ) -> AuthAttemptOutcomeDTO:
        now = datetime.now(UTC)
        row = self.rows.setdefault(email, _Row(now=now))

        if row.locked_until is not None and row.locked_until > now:
            return AuthAttemptOutcomeDTO(locked=True, locked_until=row.locked_until)

        if valid:
            row.failed_count = 0
            row.locked_until = None
            return _NOT_LOCKED

        if now - row.window_started_at > SIGN_IN_ATTEMPT_WINDOW:
            row.failed_count = 1
            row.window_started_at = now
            row.locked_until = None
            return _NOT_LOCKED

        if row.failed_count + 1 >= SIGN_IN_MAX_FAILED_ATTEMPTS:
            row.failed_count += 1
            row.locked_until = now + SIGN_IN_LOCKOUT_DURATION
            return AuthAttemptOutcomeDTO(locked=True, locked_until=row.locked_until)

        row.failed_count += 1
        return _NOT_LOCKED
