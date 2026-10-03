"""Turns a stored event into what every caller reads: its next occurrence,
status and words, all of which depend on now. Pure."""

from dataclasses import replace
from datetime import datetime
from zoneinfo import ZoneInfo

from app.domains.events.interfaces.dtos import EventDTO, StoredEventDTO, UserClockDTO
from app.domains.events.services.schedule import (
    alert_fires_at,
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
    # One lead until slice 2's alert list reaches the API (4.2, T-2.4).
    lead = stored.alert_leads_minutes[0] if stored.alert_leads_minutes else None
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
        alert_lead_minutes=lead,
        alert_text=describe_alert(lead_minutes=lead) if lead is not None else None,
        alert_fires_at=(
            alert_fires_at(
                schedule=stored.schedule,
                resolved=resolved,
                lead_minutes=lead,
                default_reminder_time=clock.default_reminder_time,
            )
            if lead is not None
            else None
        ),
        origin=stored.origin,
        original_input=stored.original_input,
        created_at=stored.created_at,
        updated_at=stored.updated_at,
    )


def with_notes(*, event: EventDTO, notes: tuple[str, ...]) -> EventDTO:
    return replace(event, when_notes=notes)
