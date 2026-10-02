"""Reads one `/add-event` sentence and hands it to events. Epic 007, FR-1.

Shared by ``SubmitCaptureInteractor`` and ``AnswerPendingCaptureInteractor``,
as ``ReminderCaptureService`` is: a question answered later runs the same
reading as a sentence typed whole, so the two cannot disagree.
"""

from dataclasses import dataclass, replace
from datetime import date, time
from typing import Any, cast
from uuid import UUID

from app.domains.capture.constants import (
    EVENT_EXTRACTION_INSTRUCTION,
    EVENT_EXTRACTION_SCHEMA,
)
from app.domains.capture.interfaces.ports import EventPort, ExtractionPort
from app.domains.events.public import (
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsAlertChoice,
    EventNeedsDate,
)
from app.domains.gateway.public import (
    Extraction,
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)


@dataclass(frozen=True)
class EventNeedsTitle:
    """`/add-event` with nothing to record. Capture asks what."""


@dataclass(frozen=True)
class ChosenAlert:
    """FR-16's answer: keep this one lead, or none."""

    lead_minutes: int | None


EventCaptureOutcome = (
    EventDTO
    | EventLimitReached
    | EventNeedsDate
    | EventNeedsAlertChoice
    | EventNeedsTitle
    | UserLimitReached
    | ProviderUnavailable
    | ProviderTimeout
    | SharedQuotaExhausted
    | MalformedResult
)


class EventCaptureService:
    def __init__(self, *, event_port: EventPort, extraction: ExtractionPort) -> None:
        self.event_port = event_port
        self.extraction = extraction

    async def capture_event(
        self,
        *,
        user_id: UUID,
        argument_text: str,
        original_input: str,
        chosen_alert: ChosenAlert | None = None,
    ) -> EventCaptureOutcome:
        """Extract the fields, then create. A gateway failure comes back as the
        gateway's own member, unmapped, as `/remind` returns it."""
        if not argument_text.strip():
            return EventNeedsTitle()
        extraction_result = await self.extraction.extract(
            user_id=user_id,
            prompt=argument_text,
            schema=EVENT_EXTRACTION_SCHEMA,
            instruction=EVENT_EXTRACTION_INSTRUCTION,
        )
        if not isinstance(extraction_result, Extraction):
            return extraction_result
        fields = read_event_fields(
            extracted_fields=cast(dict[str, Any], extraction_result.data)
        )
        if fields is None:
            return EventNeedsTitle()
        if chosen_alert is not None:
            leads = (
                (chosen_alert.lead_minutes,)
                if chosen_alert.lead_minutes is not None
                else ()
            )
            fields = replace(fields, alert_leads_minutes=leads)
        return await self.event_port.create_event(
            user_id=user_id, fields=fields, original_input=original_input
        )


def read_event_fields(*, extracted_fields: dict[str, Any]) -> EventFields | None:
    """The model's output as typed fields. A value that does not parse is
    treated as not said, so the rules for missing input apply to it."""
    title = extracted_fields.get("title")
    if not isinstance(title, str) or not title.strip():
        return None
    return EventFields(
        title=title.strip(),
        start_date=_read_date(raw=extracted_fields.get("start_date")),
        has_year=extracted_fields.get("has_year") is True,
        start_time=_read_time(raw=extracted_fields.get("start_time")),
        end_date=_read_date(raw=extracted_fields.get("end_date")),
        end_time=_read_time(raw=extracted_fields.get("end_time")),
        location=_read_text(raw=extracted_fields.get("location")),
        description=_read_text(raw=extracted_fields.get("description")),
        repeat_yearly=extracted_fields.get("repeat_yearly") is True,
        alert_leads_minutes=_read_leads(
            raw=extracted_fields.get("alert_leads_minutes")
        ),
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


def _read_text(*, raw: object) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _read_leads(*, raw: object) -> tuple[int, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(
        int(lead)
        for lead in raw
        if isinstance(lead, int | float) and not isinstance(lead, bool)
    )
