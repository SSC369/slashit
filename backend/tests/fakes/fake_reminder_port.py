"""An in-memory ReminderPort for capture, backed by the real create rules.

It runs the real ``CreateReminderInteractor`` over an in-memory repository, so
a capture test sees the same outcomes (needs when, limit reached) the product
does, without a database.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from app.domains.capture.interfaces.ports import ExtractionPort
from app.domains.capture.services.reminder_capture import ReminderCaptureService
from app.domains.reminders.interactors.create_reminder import CreateReminderInteractor
from app.domains.reminders.public import (
    ReminderDTO,
    ReminderFields,
    ReminderLimitReached,
    ReminderNeedsWhen,
)
from tests.fakes.fake_reminder_repository import FakeReminderRepository
from tests.fakes.fake_user_clock_port import FakeUserClockPort


class FakeReminderPort:
    def __init__(
        self,
        *,
        now_provider: Callable[[], datetime] = lambda: datetime.now(UTC),
        timezone: str = "Asia/Kolkata",
    ) -> None:
        self.repository = FakeReminderRepository()
        self.create_interactor = CreateReminderInteractor(
            reminder_repository=self.repository,
            user_clock=FakeUserClockPort(timezone=timezone),
            now_provider=now_provider,
        )

    async def create_reminder(
        self, *, user_id: UUID, fields: ReminderFields, original_input: str
    ) -> ReminderDTO | ReminderLimitReached | ReminderNeedsWhen:
        return await self.create_interactor.create_reminder(
            user_id=user_id,
            fields=fields,
            origin="command",
            original_input=original_input,
        )

    async def list_active(self, *, user_id: UUID) -> list[ReminderDTO]:
        rows = await self.repository.list_for_user(user_id=user_id, search=None)
        return [row for row in rows if row.state != "done"]


def fake_reminder_capture(
    *, extraction: ExtractionPort, reminder_port: FakeReminderPort | None = None
) -> ReminderCaptureService:
    return ReminderCaptureService(
        reminder_port=reminder_port or FakeReminderPort(), extraction=extraction
    )
