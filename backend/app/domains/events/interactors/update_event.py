"""FR-28: edit every field of an event. FR-11, FR-21, FR-22, FR-31."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from app.domains.events.constants import (
    MAX_DESCRIPTION_LENGTH,
    MAX_LOCATION_LENGTH,
    MAX_TITLE_LENGTH,
    MAX_UPCOMING_EVENTS,
)
from app.domains.events.graphql.errors import (
    EventField,
    EventInvalidError,
    EventInvalidReason,
    EventNotFoundError,
)
from app.domains.events.interactors.dtos import UpdateEventInputDTO
from app.domains.events.interfaces.dtos import (
    EventEdit,
    EventLimitReached,
    EventUpdatedDTO,
    EventWrite,
    StoredEventDTO,
    UserClockDTO,
)
from app.domains.events.interfaces.ports import (
    EventAnalyticsPort,
    EventEmbedQueue,
    UserClockPort,
)
from app.domains.events.interfaces.repositories import EventRepository
from app.domains.events.services.alert_arming import ArmedEvent, EventAlertArming
from app.domains.events.services.event_analytics import (
    record_alerts_not_set,
    record_event_edited,
)
from app.domains.events.services.presenter import present_event
from app.domains.events.services.schedule import (
    LocalSchedule,
    normalise_leads,
    resolve,
)


class UpdateEventInteractor:
    def __init__(
        self,
        *,
        event_repository: EventRepository,
        user_clock: UserClockPort,
        alert_arming: EventAlertArming,
        embed_queue: EventEmbedQueue,
        analytics: EventAnalyticsPort,
        now_provider: Callable[[], datetime],
    ) -> None:
        self.event_repository = event_repository
        self.user_clock = user_clock
        self.alert_arming = alert_arming
        self.embed_queue = embed_queue
        self.analytics = analytics
        self.now_provider = now_provider

    async def update_event(self, *, dto: UpdateEventInputDTO) -> EventUpdatedDTO:
        """Replace the event's fields. A yearly event's edit is the series'
        (FR-11). A change to the title, the schedule or the alerts sets the
        alerts again as one set, each by its own lead (FR-21, FR-22); a
        location or description edit leaves them alone.

        Raises:
            EventInvalidError: the title is empty, a text is over its limit,
                the end is before the start, or the edit would make a 501st
                upcoming event.
            EventNotFoundError: no live event with this id is theirs.
        """
        edit = self._trim_edit(edit=dto.edit)
        self._validate_texts(edit=edit)
        self._validate_end(edit=edit)

        previous = await self._get_live_event(dto=dto)
        clock = await self.user_clock.get_user_clock(user_id=dto.user_id)
        now = self.now_provider()
        updated = await self._store_edit(
            dto=dto, edit=edit, previous=previous, clock=clock, now=now
        )
        armed = await self._rearm_if_pending(updated=updated, clock=clock, now=now)
        await self._queue_embed_if_words_changed(previous=previous, updated=updated)
        await record_event_edited(
            analytics=self.analytics, previous=previous, updated=updated, now=now
        )
        await record_alerts_not_set(
            analytics=self.analytics,
            user_id=dto.user_id,
            alerts_not_set=armed.alerts_not_set,
        )
        return EventUpdatedDTO(
            event=present_event(stored=armed.stored, clock=clock, now=now),
            alerts_not_set=armed.alerts_not_set,
        )

    def _trim_edit(self, *, edit: EventEdit) -> EventEdit:
        return replace(
            edit,
            title=edit.title.strip(),
            location=(edit.location or "").strip() or None,
            description=(edit.description or "").strip() or None,
        )

    def _validate_texts(self, *, edit: EventEdit) -> None:
        if not edit.title:
            raise EventInvalidError(
                field=EventField.TITLE, reason=EventInvalidReason.EMPTY
            )
        for field, text, limit in (
            (EventField.TITLE, edit.title, MAX_TITLE_LENGTH),
            (EventField.LOCATION, edit.location, MAX_LOCATION_LENGTH),
            (EventField.DESCRIPTION, edit.description, MAX_DESCRIPTION_LENGTH),
        ):
            if text is not None and len(text) > limit:
                raise EventInvalidError(field=field, reason=EventInvalidReason.TOO_LONG)

    def _validate_end(self, *, edit: EventEdit) -> None:
        """An end date before the start is refused, as `EventEditInvalid`
        draws. An end time before the start on the same day is overnight
        (FR-7), and an end time needs a start time."""
        if edit.end_date is not None and edit.end_date < edit.start_date:
            raise EventInvalidError(
                field=EventField.END, reason=EventInvalidReason.END_BEFORE_START
            )
        if edit.end_time is not None and edit.start_time is None:
            raise EventInvalidError(
                field=EventField.END, reason=EventInvalidReason.END_BEFORE_START
            )

    async def _get_live_event(self, *, dto: UpdateEventInputDTO) -> StoredEventDTO:
        previous = await self.event_repository.get_by_id(
            user_id=dto.user_id, event_id=dto.event_id
        )
        if previous is None:
            raise EventNotFoundError()
        return previous

    async def _store_edit(
        self,
        *,
        dto: UpdateEventInputDTO,
        edit: EventEdit,
        previous: StoredEventDTO,
        clock: UserClockDTO,
        now: datetime,
    ) -> StoredEventDTO:
        schedule = LocalSchedule(
            start_date=edit.start_date,
            start_time=edit.start_time,
            end_date=edit.end_date,
            end_time=edit.end_time,
            repeat_yearly=edit.repeat_yearly,
            timezone=clock.timezone,
        )
        resolved = resolve(schedule=schedule, now=now)
        leads = normalise_leads(leads=edit.alert_leads_minutes).leads
        outcome = await self.event_repository.update_event_if_upcoming_below(
            user_id=dto.user_id,
            event_id=dto.event_id,
            write=EventWrite(
                title=edit.title,
                location=edit.location,
                description=edit.description,
                schedule=schedule,
                starts_at=resolved.starts_at,
                ends_at=resolved.ends_at,
                alert_leads_minutes=leads,
                origin="edit",
                original_input=None,
                # A set still pending from an earlier failure stays pending.
                alerts_pending=previous.alerts_pending
                or _changes_alerts(
                    previous=previous, title=edit.title, schedule=schedule, leads=leads
                ),
            ),
            limit=MAX_UPCOMING_EVENTS,
            now=now,
        )
        if isinstance(outcome, EventLimitReached):
            raise EventInvalidError(
                field=EventField.DATE, reason=EventInvalidReason.LIMIT
            )
        if outcome is None:
            raise EventNotFoundError()
        return outcome

    async def _queue_embed_if_words_changed(
        self, *, previous: StoredEventDTO, updated: StoredEventDTO
    ) -> None:
        """The repository cleared the old vector; the job writes the new one
        (005 AD-7)."""
        previous_words = (previous.title, previous.location, previous.description)
        updated_words = (updated.title, updated.location, updated.description)
        if previous_words != updated_words:
            await self.embed_queue.queue_event_embed(
                user_id=updated.user_id, event_id=updated.id, delay_seconds=0
            )

    async def _rearm_if_pending(
        self, *, updated: StoredEventDTO, clock: UserClockDTO, now: datetime
    ) -> ArmedEvent:
        """A location or description edit leaves the alerts as they are."""
        if not updated.alerts_pending:
            return ArmedEvent(stored=updated, alerts_not_set=())
        return await self.alert_arming.arm_alerts(
            stored=updated, clock=clock, origin="edit", now=now
        )


def _changes_alerts(
    *,
    previous: StoredEventDTO,
    title: str,
    schedule: LocalSchedule,
    leads: tuple[int, ...],
) -> bool:
    """The alert rows carry the title and fire at times the schedule and
    leads decide; nothing else an edit changes touches them (FR-21, FR-22)."""
    return (
        previous.title != title
        or previous.schedule != schedule
        or previous.alert_leads_minutes != leads
    )
