"""Reminders' GraphQL inputs."""

from datetime import date
from enum import Enum

import strawberry

from app.domains.reminders.interfaces.dtos import ReminderRepeatKind


@strawberry.input
class UpdateReminderInput:
    """The edit form, whole. `localTime` is "HH:MM", 24-hour."""

    description: str
    start_date: date
    local_time: str
    repeat_kind: ReminderRepeatKind
    repeat_interval: int = 1
    repeat_weekdays: list[int] = strawberry.field(default_factory=list)


@strawberry.enum
class SnoozeChoice(Enum):
    """FR-21's three choices, as the pop-up and panel offer them."""

    TEN_MINUTES = "ten_minutes"
    ONE_HOUR = "one_hour"
    TOMORROW = "tomorrow"
