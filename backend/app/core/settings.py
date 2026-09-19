"""Application settings.

This module is the only place in the backend that reads the environment.
Requirement FR-1 of the AI gateway PRD depends on that being true, so no other
module calls ``os.environ`` or ``os.getenv``.
"""

from functools import lru_cache
from typing import Literal
from urllib.parse import unquote, urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

_ASYNC_DRIVER_PREFIX = "postgresql+asyncpg://"


class Settings(BaseSettings):
    """Configuration read from the environment, validated at startup.

    ``extra="forbid"`` is deliberate. A misspelled key in ``.env`` stops the
    process rather than silently leaving a default in place, which is how a
    production environment ends up running on a developer's default.

    No secret carries a default value. A missing secret must stop the process,
    never fall back to something that happens to work.
    """

    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = False
    log_level: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = "INFO"

    # --- Slice 3: the gateway ---
    gemini_api_key: str
    gemini_model: str = "gemini-3.6-flash"
    # Kill switch. False refuses every extraction without calling out.
    gateway_enabled: bool = True

    # --- Slice 2: identity and isolation ---
    database_url: str
    supabase_url: str
    supabase_jwks_url: str
    # The anon/publishable key, same one the frontend embeds. Not a secret:
    # it authorises calls to Supabase's public Auth API, nothing more. Used
    # by SupabaseAuthService for the server-side sign-in call (FR-17).
    supabase_publishable_key: str
    db_pool_size: int = 5
    db_pool_max_overflow: int = 5
    # Supabase caches its JWKS for ten minutes. Caching longer than the issuer
    # does risks rejecting valid tokens signed with a freshly rotated key.
    jwks_cache_seconds: int = 600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        case_sensitive=False,
    )

    @property
    def async_database_url(self) -> str:
        """``database_url`` with the asyncpg driver named, as SQLAlchemy wants."""
        _, _, rest = self.database_url.partition("://")
        return f"{_ASYNC_DRIVER_PREFIX}{rest}"

    @property
    def jwt_issuer(self) -> str:
        """The issuer Supabase stamps on every token it signs."""
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    def secret_values(self) -> frozenset[str]:
        """Every secret this process holds, for the log redactor.

        Requirement FR-3 says no application log records the provider
        credential, at any level. This set is what makes that true: the
        structlog processor strips every value in it before anything renders.

        **A secret added to ``Settings`` without being added here is a defect.**
        """
        secrets = {self.gemini_api_key}

        # A connection error renders the DSN, and the DSN carries the password.
        # Both encoded and decoded forms: the DSN carries one, an exception may
        # carry the other.
        password = urlsplit(self.database_url).password
        if password:
            secrets.update({password, unquote(password)})

        # An empty string would redact every character of every log line.
        return frozenset(secret for secret in secrets if secret)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, built once."""
    return Settings()
