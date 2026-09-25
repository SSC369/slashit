"""Reminders' failure outcomes, as union members and exceptions together.

Both faces of an error live in this one file, per repo-rules.md sections 7.1
and 8. A missing or another user's id reads the same (NFR-6).
"""

import strawberry

from app.core.errors import DomainError


@strawberry.type
class ReminderNotFound:
    message: str


class ReminderNotFoundError(DomainError):
    gql_type = ReminderNotFound

    def __init__(self) -> None:
        super().__init__("This reminder doesn't exist or was deleted.")


@strawberry.type
class ReminderDeleted:
    """The design's `ReminderEditGone`: deleted elsewhere while being edited."""

    message: str


class ReminderDeletedError(DomainError):
    gql_type = ReminderDeleted

    def __init__(self) -> None:
        super().__init__(
            "This reminder was deleted from another tab or device while you were "
            "editing. Your edits can't be saved to it."
        )


@strawberry.type
class InvalidReminder:
    """A field the edit form must mark. `field` names it for the client."""

    message: str
    field: str


class InvalidReminderError(DomainError):
    gql_type = InvalidReminder

    def __init__(self, *, field: str, message: str) -> None:
        self.field = field
        super().__init__(message)


@strawberry.type
class ReminderTimePassed:
    """The design's `ReminderEditPast`: a one-time edit set before now."""

    message: str


class ReminderTimePassedError(DomainError):
    gql_type = ReminderTimePassed

    def __init__(self) -> None:
        super().__init__("That time has already passed. Pick a later time.")
