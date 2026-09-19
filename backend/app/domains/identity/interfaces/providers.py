"""What an auth provider must do.

`SignInInteractor` depends on this and on nothing concrete. Supabase lives
below it, inside `services/`, and no name from Supabase's SDK or REST API
appears above this line, same reasoning as gateway's `ModelProvider`.
"""

from typing import Protocol

from app.domains.identity.interfaces.dtos import AuthSessionDTO


class InvalidCredentialsProviderError(Exception):
    """The provider rejected the email/password pair."""


class EmailNotConfirmedProviderError(Exception):
    """The account exists and the password may well be right, but the email
    is not verified yet. Distinct from a wrong password: Supabase's own
    ``email_not_confirmed`` error code, not a guess at credentials."""


class ProviderUnavailableError(Exception):
    """The provider could not be reached, or returned something unexpected."""


class AuthProvider(Protocol):
    async def sign_in(self, *, email: str, password: str) -> AuthSessionDTO:
        """Exchange an email/password pair for a session.

        Raises:
            InvalidCredentialsProviderError: the pair is wrong.
            EmailNotConfirmedProviderError: the account is unverified.
            ProviderUnavailableError: network failure or an unexpected
                response shape.
        """
        ...
