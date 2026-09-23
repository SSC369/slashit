from datetime import datetime

import strawberry

from app.domains.identity.interfaces.dtos import AuthSessionDTO, ProfileDTO, SettingsDTO


@strawberry.type
class Settings:
    timezone: str
    updated_at: datetime
    # Epic 003 slice 2: the snooze menu shows "Tomorrow, 9:00 AM" (FR-21).
    # "HH:MM", 24-hour. Its control arrives with slice 3 (FR-31).
    default_reminder_time: str


def settings_dto_to_type(*, settings: SettingsDTO) -> Settings:
    return Settings(
        timezone=settings.timezone,
        updated_at=settings.updated_at,
        default_reminder_time=f"{settings.default_reminder_time:%H:%M}",
    )


@strawberry.type
class Me:
    id: strawberry.ID
    email: str
    username: str | None
    avatar_url: str | None


def profile_dto_to_type(*, profile: ProfileDTO, email: str) -> Me:
    return Me(
        id=strawberry.ID(str(profile.user_id)),
        email=email,
        username=profile.username,
        avatar_url=profile.avatar_url,
    )


@strawberry.type
class SignedIn:
    """Just enough for the client to call
    ``supabaseClient.auth.setSession({access_token, refresh_token})``."""

    access_token: str
    refresh_token: str
    expires_in: int


def session_dto_to_type(*, session: AuthSessionDTO) -> SignedIn:
    return SignedIn(
        access_token=session.access_token,
        refresh_token=session.refresh_token,
        expires_in=session.expires_in,
    )
