"""Announces a timezone change as jobs deferred by name (build plan AD-6).

Reminders and events subscribe by owning a task each (epic 007 FR-12, FR-13).
Identity never imports either, so the domain graph stays acyclic (repo-rules
§6.3, option 3).
"""

from uuid import UUID

from procrastinate.exceptions import AlreadyEnqueued

from app.core.jobs import procrastinate_app

TIMEZONE_CHANGED_TASK = "reminders.timezone_changed"
EVENTS_TIMEZONE_CHANGED_TASK = "events.timezone_changed"
# Each task its own lock prefix: one queued job per user per task.
_LOCK_PREFIXES = {
    TIMEZONE_CHANGED_TASK: "tz",
    EVENTS_TIMEZONE_CHANGED_TASK: "events-tz",
}


class ProcrastinateTimezoneChangeQueue:
    async def enqueue_timezone_change(self, *, user_id: UUID) -> None:
        # One queued job per user per task is enough: each reads the zone
        # when it runs.
        for task_name, lock_prefix in _LOCK_PREFIXES.items():
            try:
                await procrastinate_app.configure_task(
                    name=task_name, queueing_lock=f"{lock_prefix}:{user_id}"
                ).defer_async(user_id=str(user_id))
            except AlreadyEnqueued:
                continue
