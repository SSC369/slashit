"""`/add-event` and `/events` through capture. Epic 007, sub-plan 4.1 §7."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from zoneinfo import ZoneInfo

from strawberry.scalars import JSON

from app.domains.capture.adapters.events_adapter import EventsAdapter
from app.domains.capture.interactors.answer_pending_capture import (
    AnswerPendingCaptureInteractor,
)
from app.domains.capture.interactors.submit_capture import SubmitCaptureInteractor
from app.domains.capture.interfaces.dtos import (
    EventAlertChoiceAskedDTO,
    EventListDTO,
    PendingCaptureDTO,
)
from app.domains.capture.services.event_capture import EventCaptureService
from app.domains.events.interactors.create_event import CreateEventInteractor
from app.domains.events.interactors.list_events import ListEventsInteractor
from app.domains.events.public import EventDTO, EventService
from app.domains.gateway.public import Extraction, ProviderUnavailable
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_calendar_event_repository import FakeCalendarEventRepository
from tests.fakes.fake_capture_turn_repository import FakeCaptureTurnRepository
from tests.fakes.fake_event_ports import FakeEventAnalyticsPort, FakeEventUserClockPort
from tests.fakes.fake_extraction_port import FakeExtractionPort
from tests.fakes.fake_memory_port import FakeMemoryPort
from tests.fakes.fake_pending_capture_repository import FakePendingCaptureRepository
from tests.fakes.fake_reminder_port import fake_reminder_capture
from tests.fakes.fake_search_port import FakeSearchPort
from tests.fakes.fake_task_port import FakeTaskPort

NOW = datetime(2026, 10, 2, 10, 0, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(UTC)
USER = uuid.uuid4()


def _said(**fields: Any) -> Extraction:
    return Extraction(
        data=cast(JSON, fields), model="fake", input_tokens=1, output_tokens=1
    )


@dataclass
class Harness:
    submit: SubmitCaptureInteractor
    answer: AnswerPendingCaptureInteractor
    events: FakeCalendarEventRepository
    pending: FakePendingCaptureRepository
    turns: FakeCaptureTurnRepository


def _harness(*, extraction: FakeExtractionPort) -> Harness:
    events = FakeCalendarEventRepository()
    clock = FakeEventUserClockPort()
    service = EventService(
        create_event_interactor=CreateEventInteractor(
            event_repository=events,
            user_clock=clock,
            analytics=FakeEventAnalyticsPort(),
            now_provider=lambda: NOW,
        ),
        list_events_interactor=ListEventsInteractor(
            event_repository=events, user_clock=clock, now_provider=lambda: NOW
        ),
    )
    event_port = EventsAdapter(event_service=service)
    event_capture = EventCaptureService(event_port=event_port, extraction=extraction)
    pending = FakePendingCaptureRepository()
    turns = FakeCaptureTurnRepository()
    shared: dict[str, Any] = {
        "pending_capture_repository": pending,
        "capture_turn_repository": turns,
        "task_port": FakeTaskPort(),
        "extraction": extraction,
        "reminder_capture": fake_reminder_capture(extraction=extraction),
        "memory_port": FakeMemoryPort(),
        "search_port": FakeSearchPort(),
        "event_capture": event_capture,
    }
    submit = SubmitCaptureInteractor(
        analytics=FakeAnalyticsPort(),
        reminder_port=cast(Any, None),
        event_port=event_port,
        **shared,
    )
    answer = AnswerPendingCaptureInteractor(**shared)
    return Harness(
        submit=submit, answer=answer, events=events, pending=pending, turns=turns
    )


async def test_add_event_creates_and_logs_the_turn() -> None:
    """FR-1."""
    extraction = FakeExtractionPort(
        result=_said(
            title="Mom's birthday",
            start_date="2026-10-12",
            repeat_yearly=True,
            alert_leads_minutes=[1440],
        )
    )
    harness = _harness(extraction=extraction)
    outcome = await harness.submit.submit_capture(
        user_id=USER,
        raw_input="/add-event Mom's birthday October 12, remind me 1 day before",
    )
    assert isinstance(outcome, EventDTO)
    assert outcome.when_text == "Mon 12 Oct, all day"
    assert outcome.alert_lead_minutes == 1440
    assert extraction.calls == ["Mom's birthday October 12, remind me 1 day before"]
    assert harness.turns.rows[0].outcome == "event_created"
    assert harness.turns.rows[0].resulting_event_id == outcome.id


async def test_no_date_asks_then_the_answer_creates() -> None:
    """FR-2: the answer is read with the sentence it completes."""
    extraction = FakeExtractionPort(
        results=[
            _said(title="Dentist appointment"),
            _said(title="Dentist appointment", start_date="2026-10-03"),
        ]
    )
    harness = _harness(extraction=extraction)
    question = await harness.submit.submit_capture(
        user_id=USER, raw_input="/add-event Dentist appointment"
    )
    assert isinstance(question, PendingCaptureDTO)
    assert question.missing_field == "event_date"
    assert question.question_text == "When is “Dentist appointment”?"
    assert harness.events.rows == []

    event = await harness.answer.answer_pending_capture(
        user_id=USER, pending_capture_id=question.id, answer="Saturday"
    )
    assert isinstance(event, EventDTO)
    assert extraction.calls[-1] == "Dentist appointment Saturday"
    assert harness.pending.rows == {}


async def test_two_alerts_ask_which_and_the_choice_keeps_one() -> None:
    """FR-16."""
    said = _said(
        title="Sam's wedding",
        start_date="2026-11-21",
        alert_leads_minutes=[10080, 1440],
    )
    extraction = FakeExtractionPort(result=said)
    harness = _harness(extraction=extraction)
    asked = await harness.submit.submit_capture(
        user_id=USER,
        raw_input=(
            "/add-event Sam's wedding Nov 21, remind me 1 week before and 1 day before"
        ),
    )
    assert isinstance(asked, EventAlertChoiceAskedDTO)
    assert [choice.lead_minutes for choice in asked.choices] == [10080, 1440]
    assert harness.events.rows == []

    event = await harness.answer.answer_pending_capture(
        user_id=USER, pending_capture_id=asked.pending_capture_id, answer="1440"
    )
    assert isinstance(event, EventDTO)
    assert event.alert_lead_minutes == 1440


async def test_no_alert_is_a_choice() -> None:
    said = _said(title="Wedding", start_date="2026-11-21", alert_leads_minutes=[60, 30])
    harness = _harness(extraction=FakeExtractionPort(result=said))
    asked = await harness.submit.submit_capture(
        user_id=USER, raw_input="/add-event Wedding Nov 21"
    )
    assert isinstance(asked, EventAlertChoiceAskedDTO)
    event = await harness.answer.answer_pending_capture(
        user_id=USER, pending_capture_id=asked.pending_capture_id, answer="none"
    )
    assert isinstance(event, EventDTO)
    assert event.alert_lead_minutes is None


async def test_events_lists_upcoming_and_logs_the_turn() -> None:
    """FR-24."""
    harness = _harness(
        extraction=FakeExtractionPort(
            result=_said(title="Dentist", start_date="2026-10-09")
        )
    )
    await harness.submit.submit_capture(
        user_id=USER, raw_input="/add-event Dentist Oct 9"
    )
    listed = await harness.submit.submit_capture(user_id=USER, raw_input="/events")
    assert isinstance(listed, EventListDTO)
    assert [event.title for event in listed.events] == ["Dentist"]
    assert harness.turns.rows[-1].outcome == "events_listed"


async def test_a_model_outage_saves_nothing_and_refuses() -> None:
    harness = _harness(
        extraction=FakeExtractionPort(result=ProviderUnavailable(message="down"))
    )
    outcome = await harness.submit.submit_capture(
        user_id=USER, raw_input="/add-event Dentist Friday 4pm"
    )
    assert isinstance(outcome, ProviderUnavailable)
    assert harness.events.rows == []
    assert harness.turns.rows[0].outcome == "refused"
