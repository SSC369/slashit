"""An in-memory AuthAccountRepository."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class FakeUnverifiedAccount:
    user_id: UUID
    created_at: datetime


class FakeAuthAccountRepository:
    """Satisfies identity's AuthAccountRepository Protocol without
    inheriting from it."""

    def __init__(self) -> None:
        self.unverified_accounts: list[FakeUnverifiedAccount] = []
        self.emails: dict[UUID, str] = {}

    async def delete_unverified_created_before(self, *, cutoff: datetime) -> int:
        kept: list[FakeUnverifiedAccount] = []
        purged: list[FakeUnverifiedAccount] = []
        for account in self.unverified_accounts:
            (purged if account.created_at < cutoff else kept).append(account)
        self.unverified_accounts = kept
        return len(purged)

    async def get_email(self, *, user_id: UUID) -> str | None:
        return self.emails.get(user_id)
