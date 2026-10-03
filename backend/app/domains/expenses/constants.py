"""Limits for expenses. No magic values elsewhere."""

from typing import Final

# PRD FR-13. Also a check constraint in 0039_expenses.
MAX_DESCRIPTION_LENGTH: Final = 200

# FR-2, amended 2026-10-03 (dev log E-2): no limit below the storage ceiling,
# PostgreSQL's bigint, about ₹92,000 lakh crore. Past it is a typo, refused
# with a typed result rather than an overflow from the database.
MAX_AMOUNT_PAISE: Final = 2**63 - 1

# Build plan §3, in the order the PRD lists them (FR-9).
EXPENSE_CATEGORIES: Final[tuple[str, ...]] = (
    "food",
    "transport",
    "shopping",
    "bills",
    "health",
    "entertainment",
    "travel",
    "other",
)

# Slice 3's embed job fills the column; the width is fixed now (005 AD-2).
EXPENSE_EMBEDDING_DIMENSIONS: Final = 768
