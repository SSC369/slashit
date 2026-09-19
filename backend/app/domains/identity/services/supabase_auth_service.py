"""Supabase's Auth REST API. The only object in the process making this call.

A service, not an adapter, same reasoning as gateway's LangChainGeminiProvider:
this talks to a vendor and knows about no other domain. Section 4 of the
ruleset reserves ``adapters/`` for the cross-domain layer of section 6.

Uses the password grant (``/auth/v1/token?grant_type=password``), the same
endpoint ``supabase-js``'s ``signInWithPassword`` calls over HTTP. The
publishable key is the frontend's own ``VITE_SUPABASE_PUBLISHABLE_KEY``
value: public, not a secret, and the only credential this call needs.

**UNVERIFIED response shape.** Supabase's error body carries the string
identifier (``"invalid_credentials"``, ``"email_not_confirmed"``, ...) under
``error_code`` on API versions before 2024-01-01 and under ``code`` on and
after, per a 2026-09-19 search of Supabase's own docs and auth-js issue
history — this project's own API version was not checked against a live
call. ``_error_code_from`` reads both fields defensively rather than assume
one, so a wrong guess degrades to the generic InvalidCredentials outcome
rather than crashing.
"""

import httpx

from app.domains.identity.interfaces.dtos import AuthSessionDTO
from app.domains.identity.interfaces.providers import (
    EmailNotConfirmedProviderError,
    InvalidCredentialsProviderError,
    ProviderUnavailableError,
)

_SIGN_IN_TIMEOUT_SECONDS = 8.0
_EMAIL_NOT_CONFIRMED_CODE = "email_not_confirmed"


class SupabaseAuthService:
    def __init__(
        self,
        *,
        base_url: str,
        publishable_key: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.publishable_key = publishable_key
        # None in production: httpx opens a real connection. Tests inject an
        # httpx.MockTransport instead of patching the vendor SDK.
        self.transport = transport

    async def sign_in(self, *, email: str, password: str) -> AuthSessionDTO:
        try:
            async with httpx.AsyncClient(
                timeout=_SIGN_IN_TIMEOUT_SECONDS, transport=self.transport
            ) as client:
                response = await client.post(
                    f"{self.base_url}/auth/v1/token",
                    params={"grant_type": "password"},
                    headers={"apikey": self.publishable_key},
                    json={"email": email, "password": password},
                )
        except httpx.HTTPError as error:
            raise ProviderUnavailableError() from error

        if response.status_code == 200:
            return self._session_from(body=response.json())

        if response.status_code >= 500:
            raise ProviderUnavailableError()

        if self._error_code_from(response=response) == _EMAIL_NOT_CONFIRMED_CODE:
            raise EmailNotConfirmedProviderError()

        raise InvalidCredentialsProviderError()

    def _error_code_from(self, *, response: httpx.Response) -> str | None:
        try:
            body = response.json()
        except ValueError:
            return None
        if not isinstance(body, dict):
            return None

        error_code = body.get("error_code")
        if isinstance(error_code, str):
            return error_code

        code = body.get("code")
        return code if isinstance(code, str) else None

    def _session_from(self, *, body: dict[str, object]) -> AuthSessionDTO:
        try:
            return AuthSessionDTO(
                access_token=str(body["access_token"]),
                refresh_token=str(body["refresh_token"]),
                expires_in=int(str(body["expires_in"])),
            )
        except (KeyError, ValueError, TypeError) as error:
            raise ProviderUnavailableError() from error
