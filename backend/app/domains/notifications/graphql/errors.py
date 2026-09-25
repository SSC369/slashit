"""Notifications' failure outcomes, as union members and exceptions together."""

import strawberry

from app.core.errors import DomainError


@strawberry.type
class NotificationNotFound:
    message: str


class NotificationNotFoundError(DomainError):
    """A missing id and another user's id read the same (NFR-6)."""

    gql_type = NotificationNotFound

    def __init__(self) -> None:
        super().__init__("This notification doesn't exist.")
