"""Queues email jobs on Procrastinate, by name, so this module never imports
the task back (the same pattern reminders' firing queue uses)."""

from uuid import UUID

from procrastinate.exceptions import AlreadyEnqueued

from app.core.jobs import procrastinate_app

SEND_EMAIL_TASK = "notifications.send_email"


class ProcrastinateEmailQueue:
    async def enqueue_email(self, *, delivery_id: UUID) -> bool:
        try:
            await procrastinate_app.configure_task(
                name=SEND_EMAIL_TASK, queueing_lock=f"email:{delivery_id}"
            ).defer_async(delivery_id=str(delivery_id))
        except AlreadyEnqueued:
            return False
        return True
