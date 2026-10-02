"""Events' failure outcomes, as union members and exceptions together.

Both faces of an error live in this one file, per repo-rules.md sections 7.1
and 8. A missing or another user's id reads the same (NFR-6).
"""

import strawberry

from app.core.errors import DomainError


@strawberry.type
class EventNotFound:
    message: str


class EventNotFoundError(DomainError):
    gql_type = EventNotFound

    def __init__(self) -> None:
        super().__init__("This event doesn't exist or was deleted.")
