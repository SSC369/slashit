"""Announces a timezone change as a job deferred by name (build plan AD-6).

Reminders subscribes by owning the task. Identity never imports reminders, so
the domain graph stays acyclic (repo-rules §6.3, option 3).
"""

from uuid import UUID

from procrastinate.exceptions import AlreadyEnqueued

from app.core.jobs import procrastinate_app

TIMEZONE_CHANGED_TASK = "reminders.timezone_changed"


class ProcrastinateTimezoneChangeQueue:
    async def enqueue_timezone_change(self, *, user_id: UUID) -> None:
        # One queued job per user is enough: it reads the zone when it runs.
        try:
            await procrastinate_app.configure_task(
                name=TIMEZONE_CHANGED_TASK, queueing_lock=f"tz:{user_id}"
            ).defer_async(user_id=str(user_id))
        except AlreadyEnqueued:
            return
