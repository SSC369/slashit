"""Supabase JWT verification.

The browser holds a Supabase session and sends its access token. This module
turns that token into a ``user_id`` or refuses it. Requirement FR-7 says an
unauthenticated request never reaches a provider, and this is the gate.

Verification is asymmetric: Supabase signs with ES256 or RS256 and publishes the
public keys at a JWKS endpoint. No shared secret is held, so there is no signing
key in this process to leak.
"""

import ssl
import threading
import time
from uuid import UUID

import certifi
import jwt
import structlog
from jwt import PyJWKClient

from app.core.errors import AuthenticationError
from app.core.settings import Settings

logger = structlog.get_logger(__name__)

_BEARER_PREFIX = "Bearer "
_ACCEPTED_ALGORITHMS = ("ES256", "RS256")

_jwks_client: PyJWKClient | None = None
_jwks_fetched_at: float = 0.0
_jwks_lock = threading.Lock()

# PyJWKClient fetches over urllib, which trusts only the interpreter's own CA
# file. A python.org build ships without one until "Install Certificates" runs,
# and every token was then rejected as unverifiable. certifi's bundle removes
# that dependency on how Python was installed.
_JWKS_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _get_jwks_client(settings: Settings) -> PyJWKClient:
    """Return a JWKS client, rebuilt when the cache window expires.

    Supabase caches its own JWKS for ten minutes. Holding keys longer than the
    issuer does risks rejecting a valid token signed with a rotated key, so the
    window is capped by ``jwks_cache_seconds`` rather than held indefinitely.
    """
    global _jwks_client, _jwks_fetched_at

    with _jwks_lock:
        expired = time.monotonic() - _jwks_fetched_at > settings.jwks_cache_seconds
        if _jwks_client is None or expired:
            _jwks_client = PyJWKClient(
                settings.supabase_jwks_url, ssl_context=_JWKS_SSL_CONTEXT
            )
            _jwks_fetched_at = time.monotonic()
        return _jwks_client


def reset_jwks_cache() -> None:
    """Drop the cached client. For tests, and for a forced key refresh."""
    global _jwks_client, _jwks_fetched_at
    with _jwks_lock:
        _jwks_client = None
        _jwks_fetched_at = 0.0


def extract_bearer_token(authorization_header: str | None) -> str | None:
    """Pull the token out of an Authorization header, or return None."""
    if not authorization_header:
        return None
    if not authorization_header.startswith(_BEARER_PREFIX):
        return None
    token = authorization_header[len(_BEARER_PREFIX) :].strip()
    return token or None


def verify_token(token: str, settings: Settings) -> UUID:
    """Return the user id carried by a valid Supabase token.

    Args:
        token: The raw JWT, without the ``Bearer`` prefix.
        settings: Holds the JWKS location and the expected issuer.

    Returns:
        The ``sub`` claim, which Supabase sets to the user's id.

    Raises:
        AuthenticationError: For every failure, with the same generic message.
            The reason is logged, never returned. Telling a caller whether a
            token expired or was forged tells them which half to fix.
    """
    try:
        signing_key = _get_jwks_client(settings).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=list(_ACCEPTED_ALGORITHMS),
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub", "iss"], "verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        logger.warning("auth.token_rejected", reason=type(exc).__name__)
        raise AuthenticationError("Not authenticated") from exc
    except Exception as exc:
        # A JWKS fetch failure lands here. Never fall through to accepting the
        # token: an unreachable key server means unverifiable, not trusted.
        logger.warning("auth.verification_unavailable", reason=type(exc).__name__)
        raise AuthenticationError("Not authenticated") from exc

    subject = claims.get("sub")
    try:
        return UUID(str(subject))
    except (ValueError, TypeError) as exc:
        logger.warning("auth.subject_not_a_uuid")
        raise AuthenticationError("Not authenticated") from exc


def decode_email_claim(token: str) -> str | None:
    """Read the ``email`` claim out of a token ``verify_token`` already
    accepted.

    Added for 002-authentication slice 1's ``me`` query (``Me.email``).
    Deliberately a second, unverified decode rather than a change to
    ``verify_token``'s return type: every other caller of ``verify_token``
    depends only on the user id it returns, and email is a display value,
    not a security decision, so it does not belong in that function's
    contract. Calling this before ``verify_token`` has succeeded for the
    same token would be a mistake — it does not check the signature.
    """
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        return None
    email = claims.get("email")
    return email if isinstance(email, str) and email else None
