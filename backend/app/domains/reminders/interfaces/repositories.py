"""The contract for reminder storage. Storage reads and writes; it never decides."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domains.reminders.interfaces.dtos import (
    DueReminderDTO,
    FiringDTO,
    LatenessValue,
    RecordOriginValue,
    ReminderActionValue,
    ReminderDTO,
    ReminderEmbeddingTargetDTO,
    ReminderSearchPageDTO,
    ReminderStateValue,
    UserActionValue,
)
from app.domains.reminders.services.schedule import ScheduleSpec


@dataclass(frozen=True)
class ReminderWrite:
    """Everything a create or a series edit stores. Built by an interactor."""

    description: str
    spec: ScheduleSpec
    schedule_timezone: str
    next_fire_at: datetime | None
    state: ReminderStateValue


@dataclass(frozen=True)
class RezoneWrite:
    """A reminder moved to a new timezone (FR-10, FR-11). Description, state
    and a pending snooze are not part of it: they do not move."""

    spec: ScheduleSpec
    schedule_timezone: str
    next_fire_at: datetime | None


@dataclass(frozen=True)
class FiringWrite:
    """The firing row an interactor decided on."""

    scheduled_for: datetime
    fired_at: datetime
    lateness: LatenessValue


@dataclass(frozen=True)
class ReminderStateWrite:
    """A reminder's firing state after a firing, Done or Snooze. Every field
    is written as given; the interactor carries forward what does not change."""

    state: ReminderStateValue
    next_fire_at: datetime | None
    snoozed_until: datetime | None
    last_fired_at: datetime | None
    last_action: ReminderActionValue | None


@dataclass(frozen=True)
class RecordedFiring:
    firing: FiringDTO
    # False when this occurrence had already fired: nothing was written.
    is_new: bool


class ReminderRepository(Protocol):
    async def create_reminder(
        self,
        *,
        user_id: UUID,
        write: ReminderWrite,
        origin: RecordOriginValue,
        original_input: str | None,
    ) -> ReminderDTO: ...

    async def count_active_for_user(self, *, user_id: UUID) -> int:
        """Live and not done. The 100-reminder cap reads this (FR-38)."""
        ...

    async def list_for_user(self, *, user_id: UUID) -> list[ReminderDTO]:
        """Every live reminder, unordered. Grouping is the interactor's."""
        ...

    async def get_by_id(
        self, *, user_id: UUID, reminder_id: UUID
    ) -> ReminderDTO | None:
        """A live reminder the user owns, or None."""
        ...

    async def is_deleted(self, *, user_id: UUID, reminder_id: UUID) -> bool:
        """Whether the user owns this id and it was deleted. Lets an edit tell
        "deleted meanwhile" from "never yours" (ReminderEditGone)."""
        ...

    async def update_series(
        self, *, user_id: UUID, reminder_id: UUID, write: ReminderWrite
    ) -> ReminderDTO | None: ...

    async def rezone(
        self,
        *,
        user_id: UUID,
        reminder_id: UUID,
        expected_updated_at: datetime,
        write: RezoneWrite,
    ) -> bool:
        """Writes ``write`` only if the reminder is live, not done, and its
        ``updated_at`` is still ``expected_updated_at``. False otherwise, so a
        change made since the read wins."""
        ...

    async def soft_delete(self, *, user_id: UUID, reminder_id: UUID) -> bool:
        """Sets ``deleted_at`` and clears ``next_fire_at``. False if not found."""
        ...

    async def select_due(self, *, now: datetime, limit: int) -> list[DueReminderDTO]:
        """Every user's live, not-done reminders due by ``now``. Service-role
        only: the sweep runs for all users at once (T3)."""
        ...

    async def get_for_firing(self, *, reminder_id: UUID) -> ReminderDTO | None:
        """A live, not-done reminder by id alone, for the firing job."""
        ...

    async def record_firing(
        self,
        *,
        user_id: UUID,
        reminder_id: UUID,
        expected_due_at: datetime,
        firing: FiringWrite,
        state: ReminderStateWrite,
    ) -> RecordedFiring | None:
        """In one transaction: lock the reminder, confirm it is still live and
        still due at ``expected_due_at``, insert the firing unless that
        occurrence already has one, and write ``state`` only if it was new.
        None when the reminder changed since the job was queued."""
        ...

    async def get_latest_firing(
        self, *, user_id: UUID, reminder_id: UUID
    ) -> FiringDTO | None: ...

    async def record_action(
        self,
        *,
        user_id: UUID,
        reminder_id: UUID,
        firing_id: UUID | None,
        action: UserActionValue,
        acted_at: datetime,
        state: ReminderStateWrite,
    ) -> ReminderDTO | None:
        """Writes ``state`` on a live reminder and stamps the firing's action.
        None when the reminder is not live or not theirs."""
        ...

    # Epic 005, sub-plan 4.1.
    async def search_reminders(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> ReminderSearchPageDTO: ...

    async def get_embedding(
        self, *, user_id: UUID, reminder_id: UUID
    ) -> tuple[float, ...] | None: ...

    async def get_description_needing_embedding(
        self, *, user_id: UUID, reminder_id: UUID
    ) -> str | None: ...

    async def set_embedding(
        self,
        *,
        user_id: UUID,
        reminder_id: UUID,
        description: str,
        embedding: Sequence[float],
    ) -> bool: ...

    async def select_missing_embeddings(
        self,
        *,
        updated_since: datetime | None,
        after_id: UUID | None,
        limit: int,
    ) -> list[ReminderEmbeddingTargetDTO]:
        """Live rows of every user with no vector, in id order after
        ``after_id``. For the backfill job only: reads across users."""
        ...
