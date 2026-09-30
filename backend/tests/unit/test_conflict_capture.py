"""Capture's side of a conflict, sub-plan 4.3 cases C-3.1, C-3.5, C-3.6, C-3.8
and C-3.11, with the model faked at capture's MemoryPort."""

import uuid

import pytest

from app.domains.capture.constants import CONFLICT_QUESTION
from app.domains.capture.interactors.answer_pending_capture import (
    AnswerPendingCaptureInteractor,
    PendingCaptureNotFoundError,
)
from app.domains.capture.interactors.resolve_memory_conflict import (
    ResolveMemoryConflictInteractor,
)
from app.domains.capture.interactors.submit_capture import SubmitCaptureInteractor
from app.domains.capture.interfaces.dtos import (
    MemoryConflictAskedDTO,
    PendingCaptureDTO,
    PendingCaptureGoneDTO,
)
from app.domains.memories.public import (
    ConflictAnswer,
    MemoryDiscardedDTO,
    MemorySavedDTO,
)
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_capture_turn_repository import FakeCaptureTurnRepository
from tests.fakes.fake_extraction_port import FakeExtractionPort
from tests.fakes.fake_memory_port import FakeMemoryPort, make_memory
from tests.fakes.fake_pending_capture_repository import FakePendingCaptureRepository
from tests.fakes.fake_reminder_port import FakeReminderPort, fake_reminder_capture
from tests.fakes.fake_search_port import FakeSearchPort
from tests.fakes.fake_task_port import FakeTaskPort

USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()
OLD_TEXT = "Preferred airline is Emirates"
NEW_FACT = "/remember My preferred airline is Qatar Airways"


class Harness:
    def __init__(self) -> None:
        self.turns = FakeCaptureTurnRepository()
        self.pending = FakePendingCaptureRepository()
        self.memory_port = FakeMemoryPort()
        self.old = make_memory(user_id=USER, text=OLD_TEXT)
        self.memory_port.conflict_with = [self.old]
        extraction = FakeExtractionPort()
        self.submit = SubmitCaptureInteractor(
            pending_capture_repository=self.pending,
            capture_turn_repository=self.turns,
            task_port=FakeTaskPort(),
            extraction=extraction,
            analytics=FakeAnalyticsPort(),
            reminder_port=FakeReminderPort(),
            reminder_capture=fake_reminder_capture(extraction=extraction),
            memory_port=self.memory_port,
            search_port=FakeSearchPort(),
        )
        self.answer = AnswerPendingCaptureInteractor(
            pending_capture_repository=self.pending,
            capture_turn_repository=self.turns,
            task_port=FakeTaskPort(),
            extraction=extraction,
            reminder_capture=fake_reminder_capture(extraction=extraction),
            memory_port=self.memory_port,
            search_port=FakeSearchPort(),
        )
        self.resolver = ResolveMemoryConflictInteractor(
            pending_capture_repository=self.pending,
            capture_turn_repository=self.turns,
            memory_port=self.memory_port,
        )

    async def ask(self) -> MemoryConflictAskedDTO:
        asked = await self.submit.submit_capture(user_id=USER, raw_input=NEW_FACT)
        assert isinstance(asked, MemoryConflictAskedDTO)
        return asked

    def waiting(self, asked: MemoryConflictAskedDTO) -> PendingCaptureDTO:
        return self.pending.rows[asked.pending_capture_id]


async def test_a_contradiction_waits_as_a_pending_conflict() -> None:
    """C-3.1 and C-3.5: nothing saved; the row and turn hold the new fact and
    ids, never the old memory's text."""
    harness = Harness()

    asked = await harness.ask()

    waiting = harness.waiting(asked)
    assert asked.question == CONFLICT_QUESTION
    assert asked.conflicting == [harness.old]
    assert harness.memory_port.saved == []
    assert waiting.missing_field == "memory_conflict"
    assert waiting.candidate_text == "My preferred airline is Qatar Airways"
    assert waiting.conflicting_memory_ids == (harness.old.id,)
    [turn] = harness.turns.rows
    assert turn.outcome == "question_asked"
    assert turn.question_text == CONFLICT_QUESTION
    assert turn.resulting_pending_capture_id == asked.pending_capture_id
    stored = [turn.input_text, turn.question_text, waiting.question_text]
    assert all(OLD_TEXT not in (value or "") for value in stored)


async def test_keep_new_saves_closes_the_question_and_links_the_thread() -> None:
    """C-3.3 at capture: the resolution turn carries both ids."""
    harness = Harness()
    asked = await harness.ask()

    outcome = await harness.resolver.resolve_memory_conflict(
        user_id=USER,
        pending_capture_id=asked.pending_capture_id,
        answer=ConflictAnswer.KEEP_NEW,
    )

    assert isinstance(outcome, MemorySavedDTO)
    assert harness.memory_port.forgotten == [harness.old.id]
    assert asked.pending_capture_id not in harness.pending.rows
    resolution = harness.turns.rows[-1]
    assert resolution.outcome == "memory_conflict_resolved"
    assert resolution.answer_text == "Keep the new one"
    assert resolution.resulting_memory_id == outcome.memory.id
    assert resolution.resulting_pending_capture_id == asked.pending_capture_id


async def test_keep_old_records_the_answer_and_saves_nothing() -> None:
    """C-3.4 at capture."""
    harness = Harness()
    asked = await harness.ask()

    outcome = await harness.resolver.resolve_memory_conflict(
        user_id=USER,
        pending_capture_id=asked.pending_capture_id,
        answer=ConflictAnswer.KEEP_OLD,
    )

    assert isinstance(outcome, MemoryDiscardedDTO)
    assert harness.memory_port.saved == []
    assert harness.turns.rows[-1].resulting_memory_id is None
    assert asked.pending_capture_id not in harness.pending.rows


async def test_a_second_answer_changes_nothing() -> None:
    """C-3.8, FR-13; and another user's answer is the same (T7)."""
    harness = Harness()
    asked = await harness.ask()
    from_other_user = await harness.resolver.resolve_memory_conflict(
        user_id=OTHER_USER,
        pending_capture_id=asked.pending_capture_id,
        answer=ConflictAnswer.KEEP_NEW,
    )
    await harness.resolver.resolve_memory_conflict(
        user_id=USER,
        pending_capture_id=asked.pending_capture_id,
        answer=ConflictAnswer.BOTH,
    )

    again = await harness.resolver.resolve_memory_conflict(
        user_id=USER,
        pending_capture_id=asked.pending_capture_id,
        answer=ConflictAnswer.KEEP_NEW,
    )

    assert isinstance(from_other_user, PendingCaptureGoneDTO)
    assert isinstance(again, PendingCaptureGoneDTO)
    assert harness.memory_port.answers == [ConflictAnswer.BOTH]
    assert harness.memory_port.forgotten == []


async def test_a_conflict_is_never_answered_by_typed_text() -> None:
    """answerPendingCapture refuses a conflict row: it is answered by choice."""
    harness = Harness()
    asked = await harness.ask()

    with pytest.raises(PendingCaptureNotFoundError):
        await harness.answer.answer_pending_capture(
            user_id=USER,
            pending_capture_id=asked.pending_capture_id,
            answer="Keep the new one",
        )


async def test_a_fact_given_as_an_answer_can_raise_a_conflict() -> None:
    """C-3.11: "What should Slashit remember?" is replaced by "Which is
    correct?", in one turn that holds the fact and the new pending id."""
    harness = Harness()
    harness.memory_port.conflict_with = []
    question = await harness.submit.submit_capture(user_id=USER, raw_input="/remember")
    assert isinstance(question, PendingCaptureDTO)
    harness.memory_port.conflict_with = [harness.old]

    asked = await harness.answer.answer_pending_capture(
        user_id=USER,
        pending_capture_id=question.id,
        answer="My preferred airline is Qatar Airways",
    )

    assert isinstance(asked, MemoryConflictAskedDTO)
    assert question.id not in harness.pending.rows
    assert harness.waiting(asked).command_name == "/remember"
    turn = harness.turns.rows[-1]
    assert turn.outcome == "question_asked"
    assert turn.answer_text == "My preferred airline is Qatar Airways"
    assert turn.resulting_pending_capture_id == asked.pending_capture_id


async def test_forgetting_the_saved_memory_deletes_its_question_turn() -> None:
    """C-3.6, FR-23: the question turn holds the typed fact but no memory id."""
    harness = Harness()
    asked = await harness.ask()
    outcome = await harness.resolver.resolve_memory_conflict(
        user_id=USER,
        pending_capture_id=asked.pending_capture_id,
        answer=ConflictAnswer.BOTH,
    )
    assert isinstance(outcome, MemorySavedDTO)

    deleted = await harness.turns.delete_turns_for_memories(
        user_id=USER, memory_ids=[outcome.memory.id]
    )

    assert deleted == 2
    assert harness.turns.rows == []
