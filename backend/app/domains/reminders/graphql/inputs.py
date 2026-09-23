"""Reminders' GraphQL inputs."""

from datetime import date

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
