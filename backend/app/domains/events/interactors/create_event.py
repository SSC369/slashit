"""Create one event from what a sentence said. FR-1 to FR-10, FR-14, FR-19,
FR-31, FR-33, FR-34."""

import re
from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime
from zoneinfo import ZoneInfo

import structlog

from app.domains.events.constants import (
    MAX_DESCRIPTION_LENGTH,
    MAX_LOCATION_LENGTH,
    MAX_TITLE_LENGTH,
    MAX_UPCOMING_EVENTS,
)
from app.domains.events.interactors.dtos import CreateEventInputDTO
from app.domains.events.interfaces.dtos import (
    EventDTO,
    EventFields,
    EventLimitReached,
    EventNeedsDate,
    EventWrite,
)
from app.domains.events.interfaces.ports import EventAnalyticsPort, UserClockPort
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.services.alert_arming import EventAlertArming
from app.domains.events.services.presenter import present_event
from app.domains.events.services.schedule import (
    LocalSchedule,
    NormalisedSchedule,
    SaidSchedule,
    describe_alert,
    normalise_leads,
    normalise_said_schedule,
    resolve,
)

logger = structlog.get_logger(__name__)

CreateEventOutcome = EventDTO | EventLimitReached | EventNeedsDate

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
        alert_arming: EventAlertArming,
        analytics: EventAnalyticsPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.event_repository = event_repository
        self.user_clock = user_clock
        self.alert_arming = alert_arming
        self.analytics = analytics
        self.now_provider = now_provider

    async def create_event(self, *, dto: CreateEventInputDTO) -> CreateEventOutcome:
        """Apply the date rules and store the event.

        Returns ``EventNeedsDate`` when no date was said and
        ``EventLimitReached`` at the cap; neither writes. Every alert said is
        set; one that is not comes back on the event's ``alerts_not_set``.
        All are outcomes a capture renders, not errors,
        so nothing raises.
        """
        fields = dto.fields
        title = _shorten(text=fields.title, limit=MAX_TITLE_LENGTH)
        if fields.start_date is None:
            return EventNeedsDate(title=title)
        leads = normalise_leads(leads=fields.alert_leads_minutes)
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
                alert_leads_minutes=leads.leads,
                origin=dto.origin,
                original_input=dto.original_input,
            ),
            limit=MAX_UPCOMING_EVENTS,
            now=now,
        )
        if stored is None:
            return EventLimitReached(limit=MAX_UPCOMING_EVENTS)

        armed = await self.alert_arming.arm_alerts(
            stored=stored, clock=clock, origin=dto.origin, now=now
        )
        event = present_event(stored=armed.stored, clock=clock, now=now)
        await self._record_event_created(event=event)
        return replace(
            event,
            when_notes=normalised.notes
            + _yearly_note(fields=fields, original_input=dto.original_input),
            alerts_not_set=armed.alerts_not_set,
            alert_notes=tuple(
                f"“{describe_alert(lead_minutes=lead)}” was named twice, kept once"
                for lead in leads.repeated
            ),
        )

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
                    "has_alert": bool(event.alerts),
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
