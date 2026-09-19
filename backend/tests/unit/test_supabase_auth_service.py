"""SupabaseAuthService against mocked HTTP responses.

Covers both API-version response shapes documented in the service's own
module docstring (``error_code`` and ``code``), since neither was checked
against a live call.
"""

import httpx
import pytest

from app.domains.identity.interfaces.providers import (
    EmailNotConfirmedProviderError,
    InvalidCredentialsProviderError,
    ProviderUnavailableError,
)
from app.domains.identity.services.supabase_auth_service import SupabaseAuthService


def _service(*, handler: httpx.MockTransport) -> SupabaseAuthService:
    return SupabaseAuthService(
        base_url="https://project.supabase.co/",
        publishable_key="anon-key",
        transport=handler,
    )


async def test_200_returns_a_session() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"access_token": "at", "refresh_token": "rt", "expires_in": 3600}
        )

    service = _service(handler=httpx.MockTransport(handler))

    session = await service.sign_in(email="user@example.com", password="correct")

    assert session.access_token == "at"
    assert session.refresh_token == "rt"
    assert session.expires_in == 3600


async def test_request_shape() -> None:
    """The double-slash-safe base URL, the grant type, and the apikey header."""
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200, json={"access_token": "at", "refresh_token": "rt", "expires_in": 1}
        )

    service = _service(handler=httpx.MockTransport(handler))
    await service.sign_in(email="user@example.com", password="correct")

    assert len(captured) == 1
    request = captured[0]
    assert str(request.url).startswith("https://project.supabase.co/auth/v1/token")
    assert request.url.params["grant_type"] == "password"
    assert request.headers["apikey"] == "anon-key"


async def test_400_with_error_code_field_wrong_password() -> None:
    """Pre-2024-01-01 API version shape: the string identifier is under
    error_code, and code is a numeric HTTP-style value."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400, json={"code": 400, "msg": "wrong", "error_code": "invalid_credentials"}
        )

    service = _service(handler=httpx.MockTransport(handler))

    with pytest.raises(InvalidCredentialsProviderError):
        await service.sign_in(email="user@example.com", password="wrong")


async def test_400_with_code_field_wrong_password() -> None:
    """2024-01-01-and-later API version shape: the string identifier is
    under code directly."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400, json={"code": "invalid_credentials", "message": "wrong"}
        )

    service = _service(handler=httpx.MockTransport(handler))

    with pytest.raises(InvalidCredentialsProviderError):
        await service.sign_in(email="user@example.com", password="wrong")


async def test_400_with_error_code_field_unconfirmed_email() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "code": 400,
                "msg": "not confirmed",
                "error_code": "email_not_confirmed",
            },
        )

    service = _service(handler=httpx.MockTransport(handler))

    with pytest.raises(EmailNotConfirmedProviderError):
        await service.sign_in(email="user@example.com", password="correct")


async def test_400_with_code_field_unconfirmed_email() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400, json={"code": "email_not_confirmed", "message": "not confirmed"}
        )

    service = _service(handler=httpx.MockTransport(handler))

    with pytest.raises(EmailNotConfirmedProviderError):
        await service.sign_in(email="user@example.com", password="correct")


async def test_401_with_no_recognisable_body_is_invalid_credentials() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="not json")

    service = _service(handler=httpx.MockTransport(handler))

    with pytest.raises(InvalidCredentialsProviderError):
        await service.sign_in(email="user@example.com", password="wrong")


async def test_500_raises_provider_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    service = _service(handler=httpx.MockTransport(handler))

    with pytest.raises(ProviderUnavailableError):
        await service.sign_in(email="user@example.com", password="correct")


async def test_network_failure_raises_provider_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    service = _service(handler=httpx.MockTransport(handler))

    with pytest.raises(ProviderUnavailableError):
        await service.sign_in(email="user@example.com", password="correct")


async def test_200_with_a_malformed_body_raises_provider_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"access_token": "at"})

    service = _service(handler=httpx.MockTransport(handler))

    with pytest.raises(ProviderUnavailableError):
        await service.sign_in(email="user@example.com", password="correct")
