from app.domains.identity.graphql.errors import (
    AccountLockedError,
    AccountNotVerifiedError,
    AuthProviderUnavailableError,
    InvalidCredentialsError,
)
from app.domains.identity.interactors.dtos import SignInInputDTO
from app.domains.identity.interfaces.dtos import AuthSessionDTO
from app.domains.identity.interfaces.providers import (
    AuthProvider,
    EmailNotConfirmedProviderError,
    InvalidCredentialsProviderError,
    ProviderUnavailableError,
)
from app.domains.identity.interfaces.repositories import AuthAttemptRepository


class SignInInteractor:
    def __init__(
        self,
        *,
        auth_attempt_repository: AuthAttemptRepository,
        auth_provider: AuthProvider,
    ) -> None:
        self.auth_attempt_repository = auth_attempt_repository
        self.auth_provider = auth_provider

    async def sign_in(self, *, dto: SignInInputDTO) -> AuthSessionDTO:
        """Sign a user in, enforcing FR-17's lockout in the app.

        Raises:
            AccountLockedError: too many recent failed attempts, whether
                this attempt's password was right or not.
            InvalidCredentialsError: the email/password pair is wrong.
            AccountNotVerifiedError: the account exists and the password may
                be right, but the email is not confirmed. Not counted as a
                failed attempt: it is not a password check.
            AuthProviderUnavailableError: Supabase could not be reached.
        """
        email = self._normalise_email(email=dto.email)
        await self._validate_not_locked(email=email)

        try:
            session = await self.auth_provider.sign_in(
                email=email, password=dto.password
            )
        except EmailNotConfirmedProviderError:
            raise AccountNotVerifiedError() from None
        except InvalidCredentialsProviderError:
            outcome = await self.auth_attempt_repository.record_attempt(
                email=email, valid=False
            )
            if outcome.locked:
                raise AccountLockedError(retry_after=outcome.locked_until) from None
            raise InvalidCredentialsError() from None
        except ProviderUnavailableError:
            raise AuthProviderUnavailableError() from None

        await self.auth_attempt_repository.record_attempt(email=email, valid=True)
        return session

    def _normalise_email(self, *, email: str) -> str:
        return email.strip().lower()

    async def _validate_not_locked(self, *, email: str) -> None:
        outcome = await self.auth_attempt_repository.is_locked(email=email)
        if outcome.locked:
            raise AccountLockedError(retry_after=outcome.locked_until)
