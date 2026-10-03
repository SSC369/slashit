"""Give one event its meaning vector (FR-30, 005 AD-7). Run by
`events.embed_event`."""

from app.domains.events.interactors.dtos import EmbedEventInputDTO
from app.domains.events.interfaces.ports import EventEmbeddingPort
from app.domains.events.interfaces.repositories import EventRepository


class EmbedEventFailedError(Exception):
    """The model refused. Raised so the job's retry strategy runs again; after
    the last attempt the vector stays NULL for the periodic backfill."""


class EmbedEventInteractor:
    def __init__(
        self, *, event_repository: EventRepository, embedding: EventEmbeddingPort
    ) -> None:
        self.event_repository = event_repository
        self.embedding = embedding

    async def embed_event(self, *, dto: EmbedEventInputDTO) -> bool:
        """Embed the event's current words and store the vector. False when
        there is nothing to do: gone, already embedded, or edited while the
        model ran (the next queued embed covers that).

        Raises:
            EmbedEventFailedError: the model refused.
        """
        words = await self.event_repository.get_text_needing_embedding(
            user_id=dto.user_id, event_id=dto.event_id
        )
        if words is None:
            return False
        vector = await self.embedding.embed_event_text(
            user_id=dto.user_id, text=words.as_embedding_input()
        )
        if vector is None:
            raise EmbedEventFailedError()
        return await self.event_repository.set_embedding(
            user_id=dto.user_id, event_id=dto.event_id, words=words, embedding=vector
        )
