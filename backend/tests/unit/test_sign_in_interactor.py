"""FR-17's sign-in lockout, moved into the app 2026-09-19."""

import pytest

from app.domains.identity.graphql.errors import (
    AccountLockedError,
    AccountNotVerifiedError,
    AuthProviderUnavailableError,
    InvalidCredentialsError,
)
from app.domains.identity.interactors.dtos import SignInInputDTO
from app.domains.identity.interactors.sign_in import SignInInteractor
from tests.fakes.fake_auth_attempt_repository import FakeAuthAttemptRepository
from tests.fakes.fake_auth_provider import FakeAuthProvider


def _interactor(
    *, correct_password: str | None = "correct", email_unconfirmed: bool = False
) -> tuple[SignInInteractor, FakeAuthAttemptRepository, FakeAuthProvider]:
    repository = FakeAuthAttemptRepository()
    provider = FakeAuthProvider(
        correct_password=correct_password, email_unconfirmed=email_unconfirmed
    )
    interactor = SignInInteractor(
        auth_attempt_repository=repository, auth_provider=provider
    )
    return interactor, repository, provider


async def test_correct_password_returns_a_session() -> None:
    interactor, _, _ = _interactor()

    session = await interactor.sign_in(
        dto=SignInInputDTO(email="user@example.com", password="correct")
    )

    assert session.access_token == "access-token"


async def test_email_is_normalised_before_reaching_the_provider() -> None:
    interactor, _, provider = _interactor()

    await interactor.sign_in(
        dto=SignInInputDTO(email="  User@Example.com ", password="correct")
    )

    assert provider.calls == [("user@example.com", "correct")]


async def test_wrong_password_raises_invalid_credentials() -> None:
    interactor, _, _ = _interactor()

    with pytest.raises(InvalidCredentialsError):
        await interactor.sign_in(
            dto=SignInInputDTO(email="user@example.com", password="wrong")
        )


async def test_a_correct_attempt_resets_a_prior_failed_count() -> None:
    interactor, repository, _ = _interactor()
    email = "user@example.com"

    for _ in range(4):
        with pytest.raises(InvalidCredentialsError):
            await interactor.sign_in(
                dto=SignInInputDTO(email=email, password="wrong")
            )

    await interactor.sign_in(dto=SignInInputDTO(email=email, password="correct"))

    outcome = await repository.is_locked(email=email)
    assert outcome.locked is False
    # A 5th wrong attempt right after should not be an immediate lock, since
    # the counter was reset by the correct sign-in above.
    with pytest.raises(InvalidCredentialsError):
        await interactor.sign_in(dto=SignInInputDTO(email=email, password="wrong"))


async def test_fifth_failed_attempt_locks_the_account() -> None:
    interactor, _, _ = _interactor()
    email = "user@example.com"

    for _ in range(4):
        with pytest.raises(InvalidCredentialsError):
            await interactor.sign_in(
                dto=SignInInputDTO(email=email, password="wrong")
            )

    with pytest.raises(AccountLockedError):
        await interactor.sign_in(dto=SignInInputDTO(email=email, password="wrong"))


async def test_a_locked_account_never_reaches_the_provider() -> None:
    """Not even a subsequent correct password calls the provider."""
    interactor, _, provider = _interactor()
    email = "user@example.com"
    for _ in range(5):
        with pytest.raises((InvalidCredentialsError, AccountLockedError)):
            await interactor.sign_in(
                dto=SignInInputDTO(email=email, password="wrong")
            )
    provider.calls.clear()

    with pytest.raises(AccountLockedError):
        await interactor.sign_in(dto=SignInInputDTO(email=email, password="correct"))

    assert provider.calls == [], "a locked account must not reach the provider at all"


async def test_unconfirmed_email_raises_account_not_verified_and_is_not_counted() -> (
    None
):
    interactor, repository, _ = _interactor(email_unconfirmed=True)
    email = "user@example.com"

    with pytest.raises(AccountNotVerifiedError):
        await interactor.sign_in(dto=SignInInputDTO(email=email, password="correct"))

    outcome = await repository.is_locked(email=email)
    assert outcome.locked is False


async def test_provider_unavailable_maps_to_the_gql_error_and_is_not_counted() -> None:
    interactor, repository, _ = _interactor(correct_password=None)
    email = "user@example.com"

    with pytest.raises(AuthProviderUnavailableError):
        await interactor.sign_in(dto=SignInInputDTO(email=email, password="anything"))

    outcome = await repository.is_locked(email=email)
    assert outcome.locked is False
