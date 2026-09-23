"""FR-28: edit a reminder. An edit to a repeating one changes the whole series."""

from collections.abc import Callable
from datetime import datetime
from zoneinfo import ZoneInfo

from app.domains.reminders.constants import MAX_REPEAT_INTERVAL, MIN_REPEAT_INTERVAL
from app.domains.reminders.graphql.errors import (
    InvalidReminderError,
    ReminderDeletedError,
    ReminderNotFoundError,
    ReminderTimePassedError,
)
from app.domains.reminders.interactors.dtos import UpdateReminderInputDTO
from app.domains.reminders.interfaces.dtos import ReminderDTO
from app.domains.reminders.interfaces.ports import UserClockPort
from app.domains.reminders.interfaces.repositories import (
    ReminderRepository,
    ReminderWrite,
)
from app.domains.reminders.services.schedule import (
    RepeatKind,
    ScheduleSpec,
    local_to_instant,
    next_occurrence,
)


class UpdateReminderInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        user_clock: UserClockPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.reminder_repository = reminder_repository
        self.user_clock = user_clock
        self.now_provider = now_provider

    async def update_reminder(self, *, dto: UpdateReminderInputDTO) -> ReminderDTO:
        """Replace the reminder's text and schedule, and recompute its next time.

        Raises:
            InvalidReminderError: empty text, a bad interval, or a weekly repeat
                with no day picked.
            ReminderTimePassedError: a one-time reminder set before now.
            ReminderDeletedError: it was deleted elsewhere meanwhile.
            ReminderNotFoundError: no reminder with this id is theirs.
        """
        self._validate_description(description=dto.description)
        self._validate_interval(interval=dto.repeat_interval)
        self._validate_weekdays(dto=dto)
        existing = await self._load_existing(dto=dto)
        clock = await self.user_clock.get_user_clock(user_id=dto.user_id)
        timezone = ZoneInfo(clock.timezone)
        now = self.now_provider()
        spec = self._build_spec(dto=dto, existing=existing, timezone=timezone)
        self._validate_not_passed(spec=spec, now=now)

        updated = await self.reminder_repository.update_series(
            user_id=dto.user_id,
            reminder_id=dto.reminder_id,
            write=ReminderWrite(
                description=dto.description.strip(),
                spec=spec,
                schedule_timezone=clock.timezone,
                next_fire_at=next_occurrence(spec=spec, timezone=timezone, after=now),
                state="upcoming",
            ),
        )
        if updated is None:
            raise ReminderDeletedError()
        return updated

    def _validate_description(self, *, description: str) -> None:
        if not description.strip():
            raise InvalidReminderError(
                field="description", message="Give the reminder a name."
            )

    def _validate_interval(self, *, interval: int) -> None:
        if not MIN_REPEAT_INTERVAL <= interval <= MAX_REPEAT_INTERVAL:
            raise InvalidReminderError(
                field="repeatInterval",
                message=f"Repeat every {MIN_REPEAT_INTERVAL} to {MAX_REPEAT_INTERVAL}.",
            )

    def _validate_weekdays(self, *, dto: UpdateReminderInputDTO) -> None:
        if dto.repeat_kind is not RepeatKind.WEEKLY:
            return
        if not dto.repeat_weekdays or any(
            not 0 <= day <= 6 for day in dto.repeat_weekdays
        ):
            raise InvalidReminderError(
                field="repeatWeekdays", message="Pick at least one day."
            )

    def _validate_not_passed(self, *, spec: ScheduleSpec, now: datetime) -> None:
        if spec.one_time_at is not None and spec.one_time_at <= now:
            raise ReminderTimePassedError()

    async def _load_existing(self, *, dto: UpdateReminderInputDTO) -> ReminderDTO:
        existing = await self.reminder_repository.get_by_id(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        )
        if existing is not None:
            return existing
        if await self.reminder_repository.is_deleted(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        ):
            raise ReminderDeletedError()
        raise ReminderNotFoundError()

    def _build_spec(
        self,
        *,
        dto: UpdateReminderInputDTO,
        existing: ReminderDTO,
        timezone: ZoneInfo,
    ) -> ScheduleSpec:
        kind = dto.repeat_kind
        one_time_at = None
        if kind is RepeatKind.NONE:
            one_time_at = local_to_instant(
                local_date=dto.start_date, local_time=dto.local_time, timezone=timezone
            )
        return ScheduleSpec(
            repeat_kind=kind,
            repeat_interval=1 if kind is RepeatKind.NONE else dto.repeat_interval,
            repeat_weekdays=(
                tuple(sorted(set(dto.repeat_weekdays)))
                if kind is RepeatKind.WEEKLY
                else ()
            ),
            repeat_month_day=self._month_day(dto=dto, existing=existing),
            local_time=dto.local_time,
            anchor_local_date=dto.start_date,
            one_time_at=one_time_at,
        )

    def _month_day(
        self, *, dto: UpdateReminderInputDTO, existing: ReminderDTO
    ) -> int | None:
        """Keeps "the 31st" when an edit leaves the kind and start date alone,
        even though the form shows the clamped date (30 September)."""
        if dto.repeat_kind not in (RepeatKind.MONTHLY, RepeatKind.YEARLY):
            return None
        unchanged = (
            existing.spec.repeat_kind is dto.repeat_kind
            and existing.spec.anchor_local_date == dto.start_date
        )
        if unchanged and existing.spec.repeat_month_day is not None:
            return existing.spec.repeat_month_day
        return dto.start_date.day
