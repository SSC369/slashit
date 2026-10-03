"""Turns a stored event into what every caller reads: its next occurrence,
status and words, all of which depend on now. Pure."""

from dataclasses import replace
from datetime import datetime
from zoneinfo import ZoneInfo

from app.domains.events.interfaces.dtos import (
    EventAlertDTO,
    EventDTO,
    StoredEventDTO,
    UserClockDTO,
)
from app.domains.events.services.schedule import (
    LocalSchedule,
    Resolved,
    alert_fire_times,
    describe_alert,
    describe_when,
    event_status,
    resolve,
)


def present_event(
    *, stored: StoredEventDTO, clock: UserClockDTO, now: datetime
) -> EventDTO:
    """A yearly event's stored instants may lag behind now until the roll job
    moves them (AD-4); resolving here keeps every read correct regardless."""
    resolved = resolve(schedule=stored.schedule, now=now)
    local_today = now.astimezone(ZoneInfo(clock.timezone)).date()
    alerts = present_alerts(
        schedule=stored.schedule,
        resolved=resolved,
        leads=stored.alert_leads_minutes,
        clock=clock,
    )
    return EventDTO(
        id=stored.id,
        user_id=stored.user_id,
        title=stored.title,
        location=stored.location,
        description=stored.description,
        schedule=stored.schedule,
        starts_at=resolved.starts_at,
        ends_at=resolved.ends_at,
        occurrence_date=resolved.occurrence_date,
        occurrence_end_date=resolved.occurrence_end_date,
        status=event_status(resolved=resolved, now=now),
        when_text=describe_when(
            schedule=stored.schedule, resolved=resolved, local_today=local_today
        ),
        origin=stored.origin,
        original_input=stored.original_input,
        created_at=stored.created_at,
        updated_at=stored.updated_at,
        alerts=alerts,
    )


def present_alerts(
    *,
    schedule: LocalSchedule,
    resolved: Resolved,
    leads: tuple[int, ...],
    clock: UserClockDTO,
) -> tuple[EventAlertDTO, ...]:
    """Each lead with its words and its fire time, soonest first (FR-27)."""
    return tuple(
        EventAlertDTO(
            lead_minutes=alert_time.lead_minutes,
            text=describe_alert(lead_minutes=alert_time.lead_minutes),
            fires_at=alert_time.fires_at,
        )
        for alert_time in alert_fire_times(
            schedule=schedule,
            resolved=resolved,
            leads=leads,
            default_reminder_time=clock.default_reminder_time,
        )
    )


def with_notes(*, event: EventDTO, notes: tuple[str, ...]) -> EventDTO:
    return replace(event, when_notes=notes)
