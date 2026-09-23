"""Data crossing identity's boundaries. Frozen, never a model instance."""

from dataclasses import dataclass
from datetime import datetime, time
from uuid import UUID


@dataclass(frozen=True)
class SettingsDTO:
    user_id: UUID
    timezone: str
    default_reminder_time: time
    popups_enabled: bool
    email_enabled: bool
    channels_off_warned_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ReminderSettingsDTO:
    """Published to other domains (index §4): what reminders and, from slice 2,
    notifications need to know about a user's clock and channels."""

    timezone: str
    default_reminder_time: time
    popups_enabled: bool
    email_enabled: bool
    channels_off_warned_at: datetime | None


@dataclass(frozen=True)
class ProfileDTO:
    user_id: UUID
    username: str | None
    # FR-21: set only for a Google-created account whose provider gave one.
    avatar_url: str | None
    # None when no `profiles` row exists yet (GetProfileInteractor.get_profile
    # synthesizes this DTO rather than raising, per 04.1's T-1.5 acceptance
    # check: "`me` returns `username: null` for a user with no profile row").
    # Not exposed through GraphQL's `Me` type, so a missing value never reaches
    # the client; kept honest here rather than backfilled with `now()`.
    created_at: datetime | None


@dataclass(frozen=True)
class AuthSessionDTO:
    """A successful sign-in, straight from Supabase's token response."""

    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True)
class AuthAttemptOutcomeDTO:
    """Whether the subject is locked, and until when."""

    locked: bool
    locked_until: datetime | None


@dataclass(frozen=True)
class ReminderSettingsSavedDTO:
    settings: SettingsDTO
    # FR-34: true only on the save that first turned both switches off.
    show_both_off_warning: bool
