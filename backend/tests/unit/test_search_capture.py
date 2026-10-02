"""Epic 005, sub-plan 4.1, C-5 to C-7: capture's `/search` branch (FR-1 to
FR-3, FR-21), against fakes."""

import uuid

from app.domains.capture.interactors.answer_pending_capture import (
    AnswerPendingCaptureInteractor,
)
from app.domains.capture.interactors.submit_capture import SubmitCaptureInteractor
from app.domains.capture.interfaces.dtos import PendingCaptureDTO
from app.domains.search.public import SearchResultsDTO, SearchTooLongDTO
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_capture_turn_repository import FakeCaptureTurnRepository
from tests.fakes.fake_expense_port import fake_expense_capture
from tests.fakes.fake_extraction_port import FakeExtractionPort, extraction
from tests.fakes.fake_memory_port import FakeMemoryPort
from tests.fakes.fake_pending_capture_repository import FakePendingCaptureRepository
from tests.fakes.fake_reminder_port import FakeReminderPort, fake_reminder_capture
from tests.fakes.fake_search_port import FakeSearchPort
from tests.fakes.fake_task_port import FakeTaskPort

USER = uuid.uuid4()


class Harness:
    def __init__(self) -> None:
        self.turns = FakeCaptureTurnRepository()
        self.pending = FakePendingCaptureRepository()
        self.search_port = FakeSearchPort()
        extraction_port = FakeExtractionPort(result=extraction())
        self.submit = SubmitCaptureInteractor(
            pending_capture_repository=self.pending,
            capture_turn_repository=self.turns,
            task_port=FakeTaskPort(),
            extraction=extraction_port,
            analytics=FakeAnalyticsPort(),
            reminder_port=FakeReminderPort(),
            reminder_capture=fake_reminder_capture(extraction=extraction_port),
            memory_port=FakeMemoryPort(),
            search_port=self.search_port,
            expense_capture=fake_expense_capture(),
        )
        self.answer = AnswerPendingCaptureInteractor(
            pending_capture_repository=self.pending,
            capture_turn_repository=self.turns,
            task_port=FakeTaskPort(),
            extraction=extraction_port,
            reminder_capture=fake_reminder_capture(extraction=extraction_port),
            memory_port=FakeMemoryPort(),
            search_port=self.search_port,
            expense_capture=fake_expense_capture(),
        )


async def test_search_with_text_searches_and_keeps_only_the_line() -> None:
    """C-7, FR-21: the turn is the typed line and nothing of the results."""
    harness = Harness()

    outcome = await harness.submit.submit_capture(
        user_id=USER, raw_input="  /search  passport  "
    )

    assert isinstance(outcome, SearchResultsDTO)
    assert harness.search_port.searches == [(USER, "passport")]
    assert [(turn.input_text, turn.outcome) for turn in harness.turns.rows] == [
        ("/search  passport", "searched")
    ]
    assert harness.turns.rows[0].answer_text is None


async def test_an_empty_search_asks_one_question_and_searches_nothing() -> None:
    """C-5, FR-2."""
    harness = Harness()

    outcome = await harness.submit.submit_capture(user_id=USER, raw_input="/search")

    assert isinstance(outcome, PendingCaptureDTO)
    assert outcome.question_text == "What should Slashit search for?"
    assert outcome.missing_field == "search_text"
    assert harness.search_port.searches == []


async def test_the_answer_runs_the_search_and_closes_the_question() -> None:
    """C-5, FR-2, FR-21: the turn keeps `/search <answer>` for Run again."""
    harness = Harness()
    asked = await harness.submit.submit_capture(user_id=USER, raw_input="/search")
    assert isinstance(asked, PendingCaptureDTO)

    outcome = await harness.answer.answer_pending_capture(
        user_id=USER, pending_capture_id=asked.id, answer=" passport "
    )

    assert isinstance(outcome, SearchResultsDTO)
    assert harness.search_port.searches == [(USER, "passport")]
    assert harness.turns.rows[-1].input_text == "/search passport"
    assert harness.turns.rows[-1].outcome == "searched"
    assert (
        await harness.pending.get_pending_capture(
            user_id=USER, pending_capture_id=asked.id
        )
        is None
    )


async def test_an_over_long_search_is_refused_and_not_searched() -> None:
    """C-6, FR-3."""
    harness = Harness()

    outcome = await harness.submit.submit_capture(
        user_id=USER, raw_input="/search " + "a" * 501
    )

    assert outcome == SearchTooLongDTO(length=501)
    assert harness.search_port.searches == []
    assert harness.turns.rows[-1].outcome == "refused"


async def test_a_search_of_exactly_the_limit_is_searched() -> None:
    harness = Harness()

    outcome = await harness.submit.submit_capture(
        user_id=USER, raw_input="/search " + "a" * 500
    )

    assert isinstance(outcome, SearchResultsDTO)


async def test_an_over_long_answer_keeps_the_question_open() -> None:
    harness = Harness()
    asked = await harness.submit.submit_capture(user_id=USER, raw_input="/search")
    assert isinstance(asked, PendingCaptureDTO)

    outcome = await harness.answer.answer_pending_capture(
        user_id=USER, pending_capture_id=asked.id, answer="a" * 501
    )

    assert outcome == SearchTooLongDTO(length=501)
    assert (
        await harness.pending.get_pending_capture(
            user_id=USER, pending_capture_id=asked.id
        )
        is not None
    )
