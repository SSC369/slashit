"""Give one reminder its meaning vector. Run by `reminders.embed_reminder`."""

from app.domains.reminders.interactors.dtos import EmbedReminderInputDTO
from app.domains.reminders.interfaces.ports import ReminderEmbeddingPort
from app.domains.reminders.interfaces.repositories import ReminderRepository


class EmbedReminderFailedError(Exception):
    """The model refused. Raised so the job's retry strategy runs again; after
    the last attempt the vector stays NULL for the periodic backfill."""


class EmbedReminderInteractor:
    def __init__(
        self,
        *,
        reminder_repository: ReminderRepository,
        embedding: ReminderEmbeddingPort,
    ) -> None:
        self.reminder_repository = reminder_repository
        self.embedding = embedding

    async def embed_reminder(self, *, dto: EmbedReminderInputDTO) -> bool:
        """Embed the reminder's current description and store it. False when
        there is nothing to do: gone, already embedded, or edited while the
        model ran (the next queued embed covers that).

        Raises:
            EmbedReminderFailedError: the model refused.
        """
        description = await self.reminder_repository.get_description_needing_embedding(
            user_id=dto.user_id, reminder_id=dto.reminder_id
        )
        if description is None:
            return False
        vector = await self.embedding.embed_reminder_description(
            user_id=dto.user_id, description=description
        )
        if vector is None:
            raise EmbedReminderFailedError()
        return await self.reminder_repository.set_embedding(
            user_id=dto.user_id,
            reminder_id=dto.reminder_id,
            description=description,
            embedding=vector,
        )
