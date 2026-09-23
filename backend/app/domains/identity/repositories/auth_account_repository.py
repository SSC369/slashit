"""The only SQL in this codebase that writes to ``auth.users`` directly.

Deliberately does not use ``app.core.db.user_transaction``: that helper's
``SET LOCAL ROLE authenticated`` is what makes RLS bind for a request on a
caller's own behalf, and this delete is the opposite of that — an
admin-wide sweep that must run with whatever privileges the connecting role
already carries (rule T3, "the service-role connection bypasses every
policy silently... for migrations and background jobs"). Calling
``user_transaction`` here would drop exactly the privilege this repository
depends on.
"""

from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text


class SqlAuthAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete_unverified_created_before(self, *, cutoff: datetime) -> int:
        async with self.session.begin():
            result = cast(
                CursorResult[Any],
                await self.session.execute(
                    text(
                        "DELETE FROM auth.users "
                        "WHERE email_confirmed_at IS NULL AND created_at < :cutoff"
                    ),
                    {"cutoff": cutoff},
                ),
            )
        return result.rowcount

    async def get_email(self, *, user_id: UUID) -> str | None:
        async with self.session.begin():
            email = await self.session.scalar(
                text("SELECT email FROM auth.users WHERE id = :id"), {"id": user_id}
            )
        return str(email) if email is not None else None
