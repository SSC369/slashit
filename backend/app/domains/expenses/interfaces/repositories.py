"""Repository contracts. Protocols, so a fake needs no inheritance."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import UUID

from app.domains.expenses.interfaces.dtos import (
    CategoryTotal,
    ExpenseCategory,
    ExpenseChanges,
    ExpenseDTO,
    ExpenseOriginValue,
)


@dataclass(frozen=True)
class ExpenseWrite:
    """What a save stores."""

    amount_paise: int
    description: str
    category: ExpenseCategory
    spent_on: date
    origin: ExpenseOriginValue
    original_input: str


class ExpenseRepository(Protocol):
    async def create_expense(self, *, user_id: UUID, write: ExpenseWrite) -> ExpenseDTO:
        """Insert one expense, committed."""
        ...

    async def get_by_id(self, *, user_id: UUID, expense_id: UUID) -> ExpenseDTO | None:
        """One live expense this user owns, or None. Deleted reads as None."""
        ...

    async def list_for_user(
        self,
        *,
        user_id: UUID,
        category: ExpenseCategory | None,
        start: date | None,
        end: date | None,
    ) -> list[ExpenseDTO]:
        """Live expenses, newest ``spent_on`` first, then newest saved.
        ``start`` and ``end`` are inclusive; None leaves that side open."""
        ...

    async def update_expense(
        self, *, user_id: UUID, expense_id: UUID, changes: ExpenseChanges
    ) -> ExpenseDTO | None:
        """Apply the set fields to one live expense, or None if there is none.
        A description change clears the vector (index §4)."""
        ...

    async def sum_by_category(
        self,
        *,
        user_id: UUID,
        start: date | None,
        end: date | None,
        category: ExpenseCategory | None,
    ) -> list[CategoryTotal]:
        """Live expenses summed per category over an inclusive range, one row
        per category with anything in it, in no order."""
        ...

    async def soft_delete(self, *, user_id: UUID, expense_id: UUID) -> bool:
        """Stamp ``deleted_at`` on one live expense. False if there was none."""
        ...
