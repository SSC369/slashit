"""Create one event from what a sentence said. FR-1 to FR-10, FR-16, FR-31."""

import re
from collections.abc import Callable
from datetime import date, datetime
from zoneinfo import ZoneInfo

import structlog

from app.domains.events.constants import (
    MAX_ALERT_LEAD_MINUTES,
    MAX_DESCRIPTION_LENGTH,
    MAX_LOCATION_LENGTH,
    MAX_TITLE_LENGTH,
    MAX_UPCOMING_EVENTS,
)
from app.domains.events.interactors.dtos import CreateEventInputDTO
from app.domains.events.interfaces.dtos import (
    AlertChoiceDTO,
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsAlertChoice,
    EventNeedsDate,
    EventWrite,
)
from app.domains.events.interfaces.ports import EventAnalyticsPort, UserClockPort
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.services.presenter import present_event, with_notes
from app.domains.events.services.schedule import (
    LocalSchedule,
    NormalisedSchedule,
    SaidSchedule,
    describe_alert,
    normalise_said_schedule,
    resolve,
)

logger = structlog.get_logger(__name__)

CreateEventOutcome = (
    EventDTO | EventLimitReached | EventNeedsDate | EventNeedsAlertChoice
)

# FR-9: a title naming one of these repeats yearly. Echoed so a wrong guess
# is visible (design §8).
_YEARLY_TITLE_WORDS = ("birthday", "anniversary")
_YEARLY_SAID = re.compile(r"\b(every year|yearly|annual(ly)?)\b", re.IGNORECASE)


class CreateEventInteractor:
    def __init__(
        self,
        *,
        event_repository: EventRepository,
        user_clock: UserClockPort,
        analytics: EventAnalyticsPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.event_repository = event_repository
        self.user_clock = user_clock
        self.analytics = analytics
        self.now_provider = now_provider

    async def create_event(self, *, dto: CreateEventInputDTO) -> CreateEventOutcome:
        """Apply the date rules and store the event.

        Returns ``EventNeedsDate`` when no date was said, ``EventNeedsAlertChoice``
        when more than one alert was, and ``EventLimitReached`` at the cap.
        None of them writes. All are outcomes a capture renders, not errors,
        so nothing raises.
        """
        fields = dto.fields
        title = _shorten(text=fields.title, limit=MAX_TITLE_LENGTH)
        if fields.start_date is None:
            return EventNeedsDate(title=title)
        leads = _read_leads(leads=fields.alert_leads_minutes)
        if len(leads) > 1:
            return EventNeedsAlertChoice(
                title=title,
                choices=tuple(
                    AlertChoiceDTO(
                        lead_minutes=lead, label=describe_alert(lead_minutes=lead)
                    )
                    for lead in leads
                ),
            )

        clock = await self.user_clock.get_user_clock(user_id=dto.user_id)
        now = self.now_provider()
        normalised = normalise_said_schedule(
            said=_said_schedule(fields=fields, start_date=fields.start_date),
            local_today=now.astimezone(ZoneInfo(clock.timezone)).date(),
        )
        schedule = _local_schedule(normalised=normalised, timezone=clock.timezone)
        resolved = resolve(schedule=schedule, now=now)
        stored = await self.event_repository.create_event_if_upcoming_below(
            user_id=dto.user_id,
            write=EventWrite(
                title=title,
                location=_shorten_optional(
                    text=fields.location, limit=MAX_LOCATION_LENGTH
                ),
                description=_shorten_optional(
                    text=fields.description, limit=MAX_DESCRIPTION_LENGTH
                ),
                schedule=schedule,
                starts_at=resolved.starts_at,
                ends_at=resolved.ends_at,
                alert_lead_minutes=leads[0] if leads else None,
                origin=dto.origin,
                original_input=dto.original_input,
            ),
            limit=MAX_UPCOMING_EVENTS,
            now=now,
        )
        if stored is None:
            return EventLimitReached(limit=MAX_UPCOMING_EVENTS)

        event = present_event(stored=stored, clock=clock, now=now)
        await self._record_event_created(event=event)
        notes = normalised.notes + _yearly_note(
            fields=fields, original_input=dto.original_input
        )
        return with_notes(event=event, notes=notes)

    async def _record_event_created(self, *, event: EventDTO) -> None:
        """PRD §8. An instrumentation failure never undoes the event."""
        try:
            await self.analytics.record_event_created(
                user_id=event.user_id,
                field_presence={
                    "all_day": event.schedule.start_time is None,
                    "has_end": event.schedule.end_date is not None
                    or event.schedule.end_time is not None,
                    "has_location": event.location is not None,
                    "yearly": event.schedule.repeat_yearly,
                    "has_alert": event.alert_lead_minutes is not None,
                },
            )
        except Exception:
            # Broad on purpose: analytics must never fail a capture.
            logger.exception(
                "analytics.event_created_failed", user_id=str(event.user_id)
            )


def _said_schedule(*, fields: EventFields, start_date: date) -> SaidSchedule:
    return SaidSchedule(
        start_date=start_date,
        has_year=fields.has_year,
        start_time=fields.start_time,
        end_date=fields.end_date,
        end_time=fields.end_time,
        repeat_yearly=fields.repeat_yearly,
    )


def _local_schedule(*, normalised: NormalisedSchedule, timezone: str) -> LocalSchedule:
    return LocalSchedule(
        start_date=normalised.start_date,
        start_time=normalised.start_time,
        end_date=normalised.end_date,
        end_time=normalised.end_time,
        repeat_yearly=normalised.repeat_yearly,
        timezone=timezone,
    )


def _read_leads(*, leads: tuple[int, ...]) -> list[int]:
    """Legal leads, each once, in the order said. A lead over a year is read
    as not said rather than refused."""
    kept: list[int] = []
    for lead in leads:
        if 0 <= lead <= MAX_ALERT_LEAD_MINUTES and lead not in kept:
            kept.append(lead)
    return kept


def _yearly_note(*, fields: EventFields, original_input: str | None) -> tuple[str, ...]:
    if not fields.repeat_yearly or _YEARLY_SAID.search(original_input or ""):
        return ()
    lowered = fields.title.lower()
    for word in _YEARLY_TITLE_WORDS:
        if word in lowered:
            return (f"Read from “{word}”",)
    return ()


def _shorten(*, text: str, limit: int) -> str:
    """Cut at a word boundary with an ellipsis rather than refuse (04.1 §6)."""
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    cut = stripped[: limit - 1].rsplit(" ", 1)[0] or stripped[: limit - 1]
    return f"{cut}…"


def _shorten_optional(*, text: str | None, limit: int) -> str | None:
    if text is None or not text.strip():
        return None
    return _shorten(text=text, limit=limit)
