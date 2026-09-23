"""An in-memory ReminderRepository. Not a mock: it behaves."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.domains.reminders.interfaces.dtos import RecordOriginValue, ReminderDTO
from app.domains.reminders.interfaces.repositories import ReminderWrite
from app.domains.reminders.services.schedule import describe


class FakeReminderRepository:
    """Satisfies reminders' ReminderRepository Protocol without inheriting it."""

    def __init__(self) -> None:
        self.rows: dict[uuid.UUID, ReminderDTO] = {}
        self.deleted_ids: set[uuid.UUID] = set()

    async def create_reminder(
        self,
        *,
        user_id: uuid.UUID,
        write: ReminderWrite,
        origin: RecordOriginValue,
        original_input: str | None,
    ) -> ReminderDTO:
        now = datetime.now(UTC)
        reminder = ReminderDTO(
            id=uuid.uuid4(),
            user_id=user_id,
            description=write.description,
            spec=write.spec,
            schedule_timezone=write.schedule_timezone,
            next_fire_at=write.next_fire_at,
            state=write.state,
            last_fired_at=None,
            last_action=None,
            summary=describe(
                spec=write.spec, timezone=ZoneInfo(write.schedule_timezone), now=now
            ),
            origin=origin,
            original_input=original_input,
            created_at=now,
            updated_at=now,
        )
        self.rows[reminder.id] = reminder
        return reminder

    async def count_active_for_user(self, *, user_id: uuid.UUID) -> int:
        return sum(1 for row in self._live_for(user_id=user_id) if row.state != "done")

    async def list_for_user(
        self, *, user_id: uuid.UUID, search: str | None
    ) -> list[ReminderDTO]:
        rows = self._live_for(user_id=user_id)
        if search:
            rows = [row for row in rows if search.lower() in row.description.lower()]
        return rows

    async def get_by_id(
        self, *, user_id: uuid.UUID, reminder_id: uuid.UUID
    ) -> ReminderDTO | None:
        row = self.rows.get(reminder_id)
        if row is None or row.user_id != user_id or reminder_id in self.deleted_ids:
            return None
        return row

    async def is_deleted(self, *, user_id: uuid.UUID, reminder_id: uuid.UUID) -> bool:
        row = self.rows.get(reminder_id)
        return (
            row is not None
            and row.user_id == user_id
            and reminder_id in self.deleted_ids
        )

    async def update_series(
        self, *, user_id: uuid.UUID, reminder_id: uuid.UUID, write: ReminderWrite
    ) -> ReminderDTO | None:
        existing = await self.get_by_id(user_id=user_id, reminder_id=reminder_id)
        if existing is None:
            return None
        now = datetime.now(UTC)
        updated = replace(
            existing,
            description=write.description,
            spec=write.spec,
            schedule_timezone=write.schedule_timezone,
            next_fire_at=write.next_fire_at,
            state=write.state,
            summary=describe(
                spec=write.spec, timezone=ZoneInfo(write.schedule_timezone), now=now
            ),
            updated_at=now,
        )
        self.rows[reminder_id] = updated
        return updated

    async def soft_delete(self, *, user_id: uuid.UUID, reminder_id: uuid.UUID) -> bool:
        existing = await self.get_by_id(user_id=user_id, reminder_id=reminder_id)
        if existing is None:
            return False
        self.deleted_ids.add(reminder_id)
        self.rows[reminder_id] = replace(existing, next_fire_at=None)
        return True

    def _live_for(self, *, user_id: uuid.UUID) -> list[ReminderDTO]:
        return [
            row
            for row in self.rows.values()
            if row.user_id == user_id and row.id not in self.deleted_ids
        ]
