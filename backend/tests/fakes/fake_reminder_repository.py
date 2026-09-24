"""An in-memory ReminderRepository. Not a mock: it behaves."""

import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.domains.reminders.interfaces.dtos import (
    DueReminderDTO,
    FiringDTO,
    RecordOriginValue,
    ReminderDTO,
    UserActionValue,
)
from app.domains.reminders.interfaces.repositories import (
    FiringWrite,
    RecordedFiring,
    ReminderStateWrite,
    ReminderWrite,
    RezoneWrite,
)
from app.domains.reminders.services.firing import summarize_reminder


def _real_now() -> datetime:
    return datetime.now(UTC)


class FakeReminderRepository:
    """Satisfies reminders' ReminderRepository Protocol without inheriting it.

    Describes reminders against the test's clock, never the wall clock, so a
    "Today, 8:00 PM" assertion does not flip after 8 PM.
    """

    def __init__(self, *, now_provider: Callable[[], datetime] = _real_now) -> None:
        self.now_provider = now_provider
        self.rows: dict[uuid.UUID, ReminderDTO] = {}
        self.deleted_ids: set[uuid.UUID] = set()
        self.firings: dict[uuid.UUID, FiringDTO] = {}
        # Runs before each rezone write, so a test can change the row between
        # the interactor's read and its write, as a firing or an edit would.
        self.before_rezone: Callable[[uuid.UUID], None] | None = None

    async def create_reminder(
        self,
        *,
        user_id: uuid.UUID,
        write: ReminderWrite,
        origin: RecordOriginValue,
        original_input: str | None,
    ) -> ReminderDTO:
        now = self.now_provider()
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
            summary=summarize_reminder(
                spec=write.spec,
                timezone=ZoneInfo(write.schedule_timezone),
                now=now,
                state=write.state,
                last_fired_at=None,
                last_action=None,
                snoozed_until=None,
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
        updated = self._redescribe(
            reminder=replace(
                existing,
                description=write.description,
                spec=write.spec,
                schedule_timezone=write.schedule_timezone,
                next_fire_at=write.next_fire_at,
                state=write.state,
                snoozed_until=None,
                updated_at=self.now_provider(),
            )
        )
        self.rows[reminder_id] = updated
        return updated

    async def rezone(
        self,
        *,
        user_id: uuid.UUID,
        reminder_id: uuid.UUID,
        expected_updated_at: datetime,
        write: RezoneWrite,
    ) -> bool:
        if self.before_rezone is not None:
            self.before_rezone(reminder_id)
        existing = await self.get_by_id(user_id=user_id, reminder_id=reminder_id)
        if (
            existing is None
            or existing.state == "done"
            or existing.updated_at != expected_updated_at
        ):
            return False
        self.rows[reminder_id] = self._redescribe(
            reminder=replace(
                existing,
                spec=write.spec,
                schedule_timezone=write.schedule_timezone,
                next_fire_at=write.next_fire_at,
                updated_at=self.now_provider(),
            )
        )
        return True

    async def soft_delete(self, *, user_id: uuid.UUID, reminder_id: uuid.UUID) -> bool:
        existing = await self.get_by_id(user_id=user_id, reminder_id=reminder_id)
        if existing is None:
            return False
        self.deleted_ids.add(reminder_id)
        self.rows[reminder_id] = replace(
            existing, next_fire_at=None, snoozed_until=None
        )
        return True

    async def select_due(self, *, now: datetime, limit: int) -> list[DueReminderDTO]:
        due = [
            DueReminderDTO(reminder_id=row.id, due_at=row.next_due_at)
            for row in self.rows.values()
            if row.id not in self.deleted_ids
            and row.state != "done"
            and row.next_due_at is not None
            and row.next_due_at <= now
        ]
        return sorted(due, key=lambda item: item.due_at)[:limit]

    async def get_for_firing(self, *, reminder_id: uuid.UUID) -> ReminderDTO | None:
        row = self.rows.get(reminder_id)
        if row is None or reminder_id in self.deleted_ids or row.state == "done":
            return None
        return row

    async def record_firing(
        self,
        *,
        user_id: uuid.UUID,
        reminder_id: uuid.UUID,
        expected_due_at: datetime,
        firing: FiringWrite,
        state: ReminderStateWrite,
    ) -> RecordedFiring | None:
        row = await self.get_for_firing(reminder_id=reminder_id)
        if row is None or row.user_id != user_id or row.next_due_at != expected_due_at:
            return None
        existing = self._firing_for(
            reminder_id=reminder_id, scheduled_for=firing.scheduled_for
        )
        if existing is not None:
            return RecordedFiring(firing=existing, is_new=False)
        stored = FiringDTO(
            id=uuid.uuid4(),
            reminder_id=reminder_id,
            user_id=user_id,
            scheduled_for=firing.scheduled_for,
            fired_at=firing.fired_at,
            lateness=firing.lateness,
            action=None,
            acted_at=None,
        )
        self.firings[stored.id] = stored
        self.rows[reminder_id] = self._apply_state(row=row, state=state)
        return RecordedFiring(firing=stored, is_new=True)

    async def get_latest_firing(
        self, *, user_id: uuid.UUID, reminder_id: uuid.UUID
    ) -> FiringDTO | None:
        firings = [
            firing
            for firing in self.firings.values()
            if firing.reminder_id == reminder_id and firing.user_id == user_id
        ]
        return max(firings, key=lambda firing: firing.fired_at) if firings else None

    async def record_action(
        self,
        *,
        user_id: uuid.UUID,
        reminder_id: uuid.UUID,
        firing_id: uuid.UUID | None,
        action: UserActionValue,
        acted_at: datetime,
        state: ReminderStateWrite,
    ) -> ReminderDTO | None:
        row = await self.get_by_id(user_id=user_id, reminder_id=reminder_id)
        if row is None:
            return None
        if firing_id is not None and firing_id in self.firings:
            self.firings[firing_id] = replace(
                self.firings[firing_id], action=action, acted_at=acted_at
            )
        updated = self._apply_state(row=row, state=state)
        self.rows[reminder_id] = updated
        return updated

    def _firing_for(
        self, *, reminder_id: uuid.UUID, scheduled_for: datetime
    ) -> FiringDTO | None:
        for firing in self.firings.values():
            if (
                firing.reminder_id == reminder_id
                and firing.scheduled_for == scheduled_for
            ):
                return firing
        return None

    def _apply_state(
        self, *, row: ReminderDTO, state: ReminderStateWrite
    ) -> ReminderDTO:
        return self._redescribe(
            reminder=replace(
                row,
                state=state.state,
                next_fire_at=state.next_fire_at,
                snoozed_until=state.snoozed_until,
                last_fired_at=state.last_fired_at,
                last_action=state.last_action,
            )
        )

    def _redescribe(self, *, reminder: ReminderDTO) -> ReminderDTO:
        return replace(
            reminder,
            summary=summarize_reminder(
                spec=reminder.spec,
                timezone=ZoneInfo(reminder.schedule_timezone),
                now=self.now_provider(),
                state=reminder.state,
                last_fired_at=reminder.last_fired_at,
                last_action=reminder.last_action,
                snoozed_until=reminder.snoozed_until,
            ),
        )

    def _live_for(self, *, user_id: uuid.UUID) -> list[ReminderDTO]:
        return [
            row
            for row in self.rows.values()
            if row.user_id == user_id and row.id not in self.deleted_ids
        ]
