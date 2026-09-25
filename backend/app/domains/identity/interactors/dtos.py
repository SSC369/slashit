from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetSettingsInputDTO:
    user_id: UUID
    detected_timezone: str | None


@dataclass(frozen=True)
class UpdateTimezoneInputDTO:
    user_id: UUID
    timezone: str


@dataclass(frozen=True)
class SignInInputDTO:
    email: str
    password: str


@dataclass(frozen=True)
class UpdateReminderSettingsInputDTO:
    """FR-31, FR-32. None leaves a setting as it is."""

    user_id: UUID
    default_reminder_time: str | None
    popups_enabled: bool | None
    email_enabled: bool | None
