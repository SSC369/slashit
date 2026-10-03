"""Implements events' EventAnalyticsPort against the analytics domain."""

from uuid import UUID

from app.domains.analytics.public import RecordEventInputDTO, RecordEventInteractor


class EventAnalyticsAdapter:
    def __init__(self, *, record_event_interactor: RecordEventInteractor) -> None:
        self.record_event_interactor = record_event_interactor

    async def record_event_created(
        self, *, user_id: UUID, field_presence: dict[str, bool], alert_count: int
    ) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(
                user_id=user_id,
                event_type="event_created",
                properties={**field_presence, "alert_count": alert_count},
            )
        )

    async def record_event_edited(
        self,
        *,
        user_id: UUID,
        minutes_since_created: int,
        changed_fields: dict[str, bool],
    ) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(
                user_id=user_id,
                event_type="event_edited",
                properties={
                    **changed_fields,
                    "minutes_since_created": minutes_since_created,
                },
            )
        )

    async def record_alert_not_set(
        self, *, user_id: UUID, lead_minutes: int, is_over_cap: bool
    ) -> None:
        await self.record_event_interactor.record_event(
            dto=RecordEventInputDTO(
                user_id=user_id,
                event_type="event_alert_not_set",
                properties={"lead_minutes": lead_minutes, "is_over_cap": is_over_cap},
            )
        )
