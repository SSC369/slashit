"""The reminders domain's published surface, index §4.

Other domains reach reminders only through this class, re-exported from
``public.py`` and called through their own port and adapter (repo-rules.md
section 6). Creating delegates to the one use case that owns the rules.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from app.domains.reminders.interactors.create_reminder import (
    CreateReminderInteractor,
    CreateReminderOutcome,
)
from app.domains.reminders.interfaces.dtos import (
    RecordOriginValue,
    ReminderDTO,
    ReminderFields,
    ReminderSearchPageDTO,
)
from app.domains.reminders.interfaces.ports import ReminderEmbedQueue
from app.domains.reminders.interfaces.repositories import ReminderRepository

_FAR_FUTURE = datetime.max.replace(tzinfo=UTC)


class ReminderService:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        create_reminder_interactor: CreateReminderInteractor,
        embed_queue: ReminderEmbedQueue,
    ) -> None:
        self.reminder_repository = reminder_repository
        self.create_reminder_interactor = create_reminder_interactor
        self.embed_queue = embed_queue

    async def create_reminder(
        self,
        *,
        user_id: UUID,
        fields: ReminderFields,
        origin: RecordOriginValue,
        original_input: str | None,
    ) -> CreateReminderOutcome:
        outcome = await self.create_reminder_interactor.create_reminder(
            user_id=user_id, fields=fields, origin=origin, original_input=original_input
        )
        if isinstance(outcome, ReminderDTO):
            # Epic 005 AD-7: searchable by meaning once the job runs.
            await self.embed_queue.queue_reminder_embed(
                user_id=user_id, reminder_id=outcome.id, delay_seconds=0
            )
        return outcome

    async def list_active(self, *, user_id: UUID) -> list[ReminderDTO]:
        """FR-25, `/reminders`: live and not done. A fired one-time reminder has
        no next time and sorts first, since it needs attention."""
        reminders = await self.reminder_repository.list_for_user(user_id=user_id)
        active = [item for item in reminders if item.state != "done"]
        return sorted(
            active,
            key=lambda item: (item.state != "fired", item.next_due_at or _FAR_FUTURE),
        )

    async def list_for_records(self, *, user_id: UUID) -> list[ReminderDTO]:
        """Every live reminder, for the Records All tab. Records orders them."""
        return await self.reminder_repository.list_for_user(user_id=user_id)

    async def search_candidates(
        self,
        *,
        user_id: UUID,
        terms: Sequence[str],
        query_embedding: Sequence[float] | None,
        max_distance: float,
        limit: int,
    ) -> ReminderSearchPageDTO:
        """Epic 005: the user's live reminders a search matches, with the
        scores the search domain ranks by. Ranking is not decided here (AD-1)."""
        return await self.reminder_repository.search_reminders(
            user_id=user_id,
            terms=terms,
            query_embedding=query_embedding,
            max_distance=max_distance,
            limit=limit,
        )

    async def embedding_of(
        self, *, user_id: UUID, reminder_id: UUID
    ) -> tuple[float, ...] | None:
        """The live reminder's stored vector, for related records (005 AD-6)."""
        return await self.reminder_repository.get_embedding(
            user_id=user_id, reminder_id=reminder_id
        )
