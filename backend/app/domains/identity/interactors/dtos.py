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
