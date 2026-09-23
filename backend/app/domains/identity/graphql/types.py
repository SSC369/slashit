from datetime import datetime

import strawberry

from app.domains.identity.interfaces.dtos import (
    AuthSessionDTO,
    ProfileDTO,
    ReminderSettingsSavedDTO,
    SettingsDTO,
)


@strawberry.type
class Settings:
    timezone: str
    updated_at: datetime
    # Epic 003: "HH:MM", 24-hour (FR-31), and the two switches (FR-32).
    default_reminder_time: str
    popups_enabled: bool
    email_enabled: bool


@strawberry.type
class ReminderSettingsSaved:
    settings: Settings
    # FR-34: true only on the save that first turned both switches off.
    show_both_off_warning: bool


def settings_dto_to_type(*, settings: SettingsDTO) -> Settings:
    return Settings(
        timezone=settings.timezone,
        updated_at=settings.updated_at,
        default_reminder_time=f"{settings.default_reminder_time:%H:%M}",
        popups_enabled=settings.popups_enabled,
        email_enabled=settings.email_enabled,
    )


def reminder_settings_saved_to_type(
    *, saved: ReminderSettingsSavedDTO
) -> ReminderSettingsSaved:
    return ReminderSettingsSaved(
        settings=settings_dto_to_type(settings=saved.settings),
        show_both_off_warning=saved.show_both_off_warning,
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
