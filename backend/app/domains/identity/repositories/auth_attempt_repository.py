"""The only SQL for auth_attempts' sign_in rows.

Deliberately does not use ``app.core.db.user_transaction``: that helper's
``SET LOCAL ROLE authenticated`` drops to a role with no grant on this table
(migration 0008 grants only ``supabase_auth_admin``). This runs as the
connecting role itself, which owns the table, same reasoning as
``auth_account_repository.py``.

Ports the logic ``hook_password_verification_attempt`` used to run inside
Postgres (migration 0009, dropped by 0015) into Python, keyed by email
instead of user id. See ``0015_drop_pw_verify_hook.py`` for why.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.identity.constants import (
    SIGN_IN_ATTEMPT_WINDOW,
    SIGN_IN_LOCKOUT_DURATION,
    SIGN_IN_MAX_FAILED_ATTEMPTS,
)
from app.domains.identity.interfaces.dtos import AuthAttemptOutcomeDTO
from app.domains.identity.models import AuthAttempt

_NOT_LOCKED = AuthAttemptOutcomeDTO(locked=False, locked_until=None)


class SqlAuthAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def is_locked(self, *, email: str) -> AuthAttemptOutcomeDTO:
        # Scoped even for a plain read: an unscoped execute() autobegins a
        # transaction that is never closed, and the next session.begin() (in
        # record_attempt, same request) then raises "A transaction is
        # already begun on this Session." Found live, 2026-09-19.
        now = datetime.now(UTC)
        async with self.session.begin():
            row = await self._get_row(email=email)
        if row is None or row.locked_until is None or row.locked_until <= now:
            return _NOT_LOCKED
        return AuthAttemptOutcomeDTO(locked=True, locked_until=row.locked_until)

    async def record_attempt(self, *, email: str, valid: bool) -> AuthAttemptOutcomeDTO:
        now = datetime.now(UTC)
        async with self.session.begin():
            row = await self._get_row(email=email, for_update=True)
            if row is None:
                row = AuthAttempt(
                    id=uuid.uuid4(),
                    subject=email,
                    kind="sign_in",
                    failed_count=0,
                    window_started_at=now,
                    locked_until=None,
                )
                self.session.add(row)
                await self.session.flush()

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

    async def _get_row(
        self, *, email: str, for_update: bool = False
    ) -> AuthAttempt | None:
        statement = select(AuthAttempt).where(
            AuthAttempt.subject == email, AuthAttempt.kind == "sign_in"
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
