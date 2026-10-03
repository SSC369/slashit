"""PRD §8's instrumentation, shared by create and edit. An analytics failure
never undoes the event: every call here logs and carries on."""

from datetime import datetime
from uuid import UUID

import structlog

from app.domains.events.interfaces.dtos import AlertNotSetDTO, StoredEventDTO
from app.domains.events.interfaces.ports import EventAnalyticsPort

logger = structlog.get_logger(__name__)


async def record_alerts_not_set(
    *,
    analytics: EventAnalyticsPort,
    user_id: UUID,
    alerts_not_set: tuple[AlertNotSetDTO, ...],
) -> None:
    """One ``event_alert_not_set`` per alert, lead and reason only (T6)."""
    for alert in alerts_not_set:
        try:
            await analytics.record_alert_not_set(
                user_id=user_id,
                lead_minutes=alert.lead_minutes,
                is_over_cap=alert.reason == "cap",
            )
        except Exception:
            # Broad on purpose: analytics must never fail a save.
            logger.exception(
                "analytics.event_alert_not_set_failed", user_id=str(user_id)
            )


async def record_event_edited(
    *,
    analytics: EventAnalyticsPort,
    previous: StoredEventDTO,
    updated: StoredEventDTO,
    now: datetime,
) -> None:
    """G2's "edited within five minutes" reads ``minutes_since_created``."""
    try:
        await analytics.record_event_edited(
            user_id=updated.user_id,
            minutes_since_created=int(
                (now - previous.created_at).total_seconds() // 60
            ),
            changed_fields={
                "title_changed": previous.title != updated.title,
                "schedule_changed": previous.schedule != updated.schedule,
                "location_changed": previous.location != updated.location,
                "description_changed": previous.description != updated.description,
                "alerts_changed": previous.alert_leads_minutes
                != updated.alert_leads_minutes,
            },
        )
    except Exception:
        # Broad on purpose: analytics must never fail an edit.
        logger.exception("analytics.event_edited_failed", user_id=str(updated.user_id))
