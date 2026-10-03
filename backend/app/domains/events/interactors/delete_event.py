"""FR-29: delete an event, the whole series if it repeats (FR-11), and every
alert with it (FR-23)."""

from app.domains.events.graphql.errors import EventNotFoundError
from app.domains.events.interactors.dtos import DeleteEventInputDTO
from app.domains.events.interfaces.ports import EventAlertsPort
from app.domains.events.interfaces.repositories import EventRepository


class DeleteEventInteractor:
    def __init__(
        self, *, event_repository: EventRepository, alerts: EventAlertsPort
    ) -> None:
        self.event_repository = event_repository
        self.alerts = alerts

    async def delete_event(self, *, dto: DeleteEventInputDTO) -> None:
        """Clear the alerts, then soft-delete the event (4.2 Q1, dev log D-16):
        a failure between the two leaves the event without alerts, which the
        sweep repairs, never alerts for a deleted event.

        Raises:
            EventNotFoundError: no live event with this id is theirs.
        """
        await self._validate_live_event(dto=dto)
        await self.alerts.clear_alerts(user_id=dto.user_id, event_id=dto.event_id)
        was_deleted = await self.event_repository.soft_delete(
            user_id=dto.user_id, event_id=dto.event_id
        )
        if not was_deleted:
            raise EventNotFoundError()

    async def _validate_live_event(self, *, dto: DeleteEventInputDTO) -> None:
        event = await self.event_repository.get_by_id(
            user_id=dto.user_id, event_id=dto.event_id
        )
        if event is None:
            raise EventNotFoundError()
