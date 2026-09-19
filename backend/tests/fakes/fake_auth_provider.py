"""An in-memory AuthProvider. Not a mock: it behaves, so tests read as
behaviour."""

from app.domains.identity.interfaces.dtos import AuthSessionDTO
from app.domains.identity.interfaces.providers import (
    EmailNotConfirmedProviderError,
    InvalidCredentialsProviderError,
    ProviderUnavailableError,
)


def session() -> AuthSessionDTO:
    return AuthSessionDTO(
        access_token="access-token", refresh_token="refresh-token", expires_in=3600
    )


class FakeAuthProvider:
    """Satisfies identity's AuthProvider Protocol without inheriting from it."""

    def __init__(
        self,
        *,
        correct_password: str | None = "correct",
        email_unconfirmed: bool = False,
    ) -> None:
        self.correct_password = correct_password
        self.email_unconfirmed = email_unconfirmed
        self.calls: list[tuple[str, str]] = []

    async def sign_in(self, *, email: str, password: str) -> AuthSessionDTO:
        self.calls.append((email, password))
        if self.email_unconfirmed:
            raise EmailNotConfirmedProviderError()
        if self.correct_password is None:
            raise ProviderUnavailableError()
        if password != self.correct_password:
            raise InvalidCredentialsProviderError()
        return session()
