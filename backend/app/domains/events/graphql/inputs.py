"""Events' input types. The edit form sends every field, whole (FR-28)."""

from datetime import date

import strawberry


@strawberry.input
class EventInput:
    title: str
    location: str | None
    description: str | None
    start_date: date
    # "HH:MM", or null for all day (FR-3).
    start_time: str | None
    # Set for a multi-day event, or when the end is on a later day (FR-6, FR-7).
    end_date: date | None
    end_time: str | None
    repeat_yearly: bool
    # Every alert, in minutes before the start (FR-14, FR-22). Repeats are kept
    # once (FR-34).
    alert_leads_minutes: list[int]
