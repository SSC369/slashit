"""Limits for expenses. No magic values elsewhere."""

from typing import Final

# PRD FR-13. Also a check constraint in 0037_expenses.
MAX_DESCRIPTION_LENGTH: Final = 200

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
