"""Identity's failures, each as a union member and an exception together."""

from datetime import datetime

import strawberry

from app.core.errors import DomainError


@strawberry.type
class InvalidTimezone:
    message: str


class InvalidTimezoneError(DomainError):
    gql_type = InvalidTimezone

    def __init__(self, *, timezone: str) -> None:
        super().__init__(f'"{timezone}" is not a known timezone')


@strawberry.type
class InvalidCredentials:
    message: str


class InvalidCredentialsError(DomainError):
    gql_type = InvalidCredentials

    def __init__(self) -> None:
        super().__init__("Incorrect email or password")


@strawberry.type
class AccountLocked:
    message: str
    retry_after: datetime | None


class AccountLockedError(DomainError):
    """FR-17: too many recent failed sign-in attempts."""

    gql_type = AccountLocked

    def __init__(self, *, retry_after: datetime | None) -> None:
        self.retry_after = retry_after
        super().__init__("Too many attempts. Try again in 15 minutes.")


@strawberry.type
class AuthProviderUnavailable:
    message: str


class AuthProviderUnavailableError(DomainError):
    gql_type = AuthProviderUnavailable

    def __init__(self) -> None:
        super().__init__("Sign-in is temporarily unavailable. Try again shortly.")


@strawberry.type
class AccountNotVerified:
    message: str


class AccountNotVerifiedError(DomainError):
    """The email/password pair may well be right; the account just is not
    verified yet. Never counted as an FR-17 failed attempt."""

    gql_type = AccountNotVerified

    def __init__(self) -> None:
        super().__init__("Verify your email before signing in")


@strawberry.type
class InvalidReminderSettings:
    """A setting the form must mark. `field` names it for the client."""

    message: str
    field: str


class InvalidReminderSettingsError(DomainError):
    gql_type = InvalidReminderSettings

    def __init__(self, *, field: str, message: str) -> None:
        self.field = field
        super().__init__(message)
