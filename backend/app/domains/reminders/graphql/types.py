"""Reminders' own GraphQL types.

``Reminder`` itself lives in ``interfaces/dtos.py`` so it may cross into
capture and records; redeclaring it here would give the schema two types.
"""

import strawberry

from app.domains.reminders.interfaces.dtos import (
    Reminder,
    ReminderGroupsDTO,
    reminder_dto_to_type,
)


@strawberry.type
class ReminderGroups:
    """FR-26: the Reminders tab's three groups, each already ordered."""

    needs_attention: list[Reminder]
    upcoming: list[Reminder]
    done: list[Reminder]


@strawberry.type
class ReminderDeleteSucceeded:
    id: strawberry.ID


def reminder_groups_to_type(*, groups: ReminderGroupsDTO) -> ReminderGroups:
    return ReminderGroups(
        needs_attention=[
            reminder_dto_to_type(reminder=item) for item in groups.needs_attention
        ],
        upcoming=[reminder_dto_to_type(reminder=item) for item in groups.upcoming],
        done=[reminder_dto_to_type(reminder=item) for item in groups.done],
    )
