"""The only names other domains may import from reminders.

A domain's public surface is its contract. Adding a name here is a deliberate
act, reviewed like an API change. See backend/.claude/rules/repo-rules.md
section 6.
"""

from app.domains.reminders.interfaces.dtos import (
    AlertNotSet,
    AlertNotSetReasonValue,
    EventAlertRequest,
    Reminder,
    ReminderDTO,
    ReminderFields,
    ReminderLimitReached,
    ReminderNeedsWhen,
    ReminderSearchMatchDTO,
    ReminderSearchPageDTO,
    reminder_dto_to_type,
)
from app.domains.reminders.services.reminder_service import ReminderService
from app.domains.reminders.services.schedule import RepeatKind, ScheduleSummary

__all__ = [
    "AlertNotSet",
    "AlertNotSetReasonValue",
    "EventAlertRequest",
    "Reminder",
    "ReminderDTO",
    "ReminderFields",
    "ReminderLimitReached",
    "ReminderNeedsWhen",
    "ReminderSearchMatchDTO",
    "ReminderSearchPageDTO",
    "ReminderService",
    "RepeatKind",
    "ScheduleSummary",
    "reminder_dto_to_type",
]
