"""Reads one `/remind` sentence and hands it to reminders. Epic 003, FR-1.

Shared by ``SubmitCaptureInteractor`` and ``AnswerPendingCaptureInteractor``:
a question answered later runs the same reading as a sentence typed whole, so
the two can never disagree about what "tomorrow at 7" means.
"""

from dataclasses import dataclass
from datetime import date, time
from typing import Any, cast
from uuid import UUID

from app.domains.capture.constants import (
    REMINDER_EXTRACTION_INSTRUCTION,
    REMINDER_EXTRACTION_SCHEMA,
)
from app.domains.capture.interfaces.ports import ExtractionPort, ReminderPort
from app.domains.gateway.public import (
    Extraction,
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)
from app.domains.reminders.public import (
    ReminderDTO,
    ReminderFields,
    ReminderLimitReached,
    ReminderNeedsWhen,
    RepeatKind,
)


@dataclass(frozen=True)
class ReminderNeedsDescription:
    """`/remind` with nothing to remind about. Capture asks what."""


ReminderCaptureOutcome = (
    ReminderDTO
    | ReminderLimitReached
    | ReminderNeedsWhen
    | ReminderNeedsDescription
    | UserLimitReached
    | ProviderUnavailable
    | ProviderTimeout
    | SharedQuotaExhausted
    | MalformedResult
)


class ReminderCaptureService:
    def __init__(
        self, *, reminder_port: ReminderPort, extraction: ExtractionPort
    ) -> None:
        self.reminder_port = reminder_port
        self.extraction = extraction

    async def capture_reminder(
        self, *, user_id: UUID, argument_text: str, original_input: str
    ) -> ReminderCaptureOutcome:
        """Extract the fields, then create. A gateway failure comes back as the
        gateway's own member, unmapped, as `/add-task` returns it."""
        if not argument_text.strip():
            return ReminderNeedsDescription()
        extraction_result = await self.extraction.extract(
            user_id=user_id,
            prompt=argument_text,
            schema=REMINDER_EXTRACTION_SCHEMA,
            instruction=REMINDER_EXTRACTION_INSTRUCTION,
        )
        if not isinstance(extraction_result, Extraction):
            return extraction_result
        fields = read_reminder_fields(
            extracted_fields=cast(dict[str, Any], extraction_result.data)
        )
        if fields is None:
            return ReminderNeedsDescription()
        return await self.reminder_port.create_reminder(
            user_id=user_id, fields=fields, original_input=original_input
        )


def read_reminder_fields(*, extracted_fields: dict[str, Any]) -> ReminderFields | None:
    """The model's output as typed fields. A value that does not parse is
    treated as not said, so the rules for missing input apply to it."""
    description = extracted_fields.get("description")
    if not isinstance(description, str) or not description.strip():
        return None
    return ReminderFields(
        description=description.strip(),
        local_date=_read_date(raw=extracted_fields.get("local_date")),
        local_time=_read_time(raw=extracted_fields.get("local_time")),
        repeat_kind=_read_repeat_kind(raw=extracted_fields.get("repeat_kind")),
        repeat_interval=_read_int(raw=extracted_fields.get("repeat_interval")) or 1,
        repeat_weekdays=_read_weekdays(raw=extracted_fields.get("repeat_weekdays")),
        month_day=_read_int(raw=extracted_fields.get("day_of_month")),
    )


def _read_date(*, raw: object) -> date | None:
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _read_time(*, raw: object) -> time | None:
    if not isinstance(raw, str):
        return None
    try:
        return time.fromisoformat(raw[:5]).replace(second=0, microsecond=0)
    except ValueError:
        return None


def _read_repeat_kind(*, raw: object) -> RepeatKind:
    try:
        return RepeatKind(str(raw))
    except ValueError:
        return RepeatKind.NONE


def _read_int(*, raw: object) -> int | None:
    if isinstance(raw, bool) or not isinstance(raw, int | float):
        return None
    return int(raw)


def _read_weekdays(*, raw: object) -> tuple[int, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(
        int(day)
        for day in raw
        if isinstance(day, int | float) and not isinstance(day, bool)
    )
