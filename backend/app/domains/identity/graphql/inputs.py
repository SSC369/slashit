import strawberry


@strawberry.input
class UpdateTimezoneInput:
    timezone: str


@strawberry.input
class SignInInput:
    email: str
    password: str


@strawberry.input
class UpdateReminderSettingsInput:
    """FR-31, FR-32. A field left out keeps its value."""

    default_reminder_time: str | None = None
    popups_enabled: bool | None = None
    email_enabled: bool | None = None
