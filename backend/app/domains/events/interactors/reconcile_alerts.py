"""NFR-4: count events whose alerts are out of step, nightly.

An event's alerts are out of step while it is marked pending (dev log D-20):
moved, re-timed or being deleted, with reminders not yet holding the new set.
The 15-minute sweep arms them; one still pending after an hour means the sweep
is failing, so this job says so loudly. It reports, never repairs.
"""

from collections.abc import Callable
from datetime import datetime

import structlog

from app.domains.events.constants import ALERTS_OUT_OF_STEP_AFTER
from app.domains.events.interfaces.repositories import EventRepository

logger = structlog.get_logger(__name__)


class ReconcileAlertsInteractor:
    def __init__(
        self,
        *,
        event_repository: EventRepository,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.event_repository = event_repository
        self.now_provider = now_provider

    async def reconcile_alerts(self) -> int:
        """The count of out-of-step events, logged as a warning when above
        zero. Ids and counts only, never an event's text (T6)."""
        out_of_step = await self.event_repository.count_alerts_pending(
            updated_before=self.now_provider() - ALERTS_OUT_OF_STEP_AFTER
        )
        if out_of_step:
            logger.warning("events.alerts_out_of_step", count=out_of_step)
        else:
            logger.info("events.alerts_in_step")
        return out_of_step
