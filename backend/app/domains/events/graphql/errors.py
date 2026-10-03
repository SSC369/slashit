"""Events' failure outcomes, as union members and exceptions together.

Both faces of an error live in this one file, per repo-rules.md sections 7.1
and 8. A missing or another user's id reads the same (NFR-6).
"""

from enum import StrEnum
from uuid import UUID

import strawberry

from app.core.errors import DomainError


@strawberry.type
class EventNotFound:
    message: str


class EventNotFoundError(DomainError):
    gql_type = EventNotFound

    def __init__(self) -> None:
        super().__init__("This event doesn't exist or was deleted.")


def parse_event_id(id_: strawberry.ID) -> UUID:
    """A hand-typed URL such as /records/events/abc names no event, so it reads
    as one that does not exist, not as a server error."""
    try:
        return UUID(str(id_))
    except ValueError as error:
        raise EventNotFoundError() from error


@strawberry.enum
class EventField(StrEnum):
    TITLE = "title"
    LOCATION = "location"
    DESCRIPTION = "description"
    END = "end"
    DATE = "date"


@strawberry.enum
class EventInvalidReason(StrEnum):
    EMPTY = "empty"
    TOO_LONG = "too_long"
    END_BEFORE_START = "end_before_start"
    # FR-31: the edit would make a 501st upcoming event.
    LIMIT = "limit"


@strawberry.type
class EventInvalid:
    """FR-28: the edit form broke a rule. Nothing changed."""

    message: str
    field: EventField
    reason: EventInvalidReason


class EventInvalidError(DomainError):
    gql_type = EventInvalid

    def __init__(self, *, field: EventField, reason: EventInvalidReason) -> None:
        self.field = field
        self.reason = reason
        super().__init__(_INVALID_MESSAGES[reason])


_INVALID_MESSAGES = {
    EventInvalidReason.EMPTY: "Give the event a name.",
    EventInvalidReason.TOO_LONG: "That is longer than an event holds.",
    EventInvalidReason.END_BEFORE_START: "The end date is before the start date.",
    EventInvalidReason.LIMIT: (
        "You have 500 upcoming events, the most Slashit holds. Delete one you "
        "no longer need, then save again. Past events do not count."
    ),
}
