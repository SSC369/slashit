"""Capture's memory commands, sub-plan 4.1 cases C-1, C-3, C-4 and FR-9's turn."""

import uuid

import pytest

from app.domains.capture.constants import FACT_QUESTION
from app.domains.capture.interactors.answer_pending_capture import (
    AnswerPendingCaptureInteractor,
)
from app.domains.capture.interactors.submit_capture import SubmitCaptureInteractor
from app.domains.capture.interfaces.dtos import PendingCaptureDTO
from app.domains.gateway.public import ProviderUnavailable
from app.domains.memories.public import (
    MemoryListDTO,
    MemorySavedDTO,
    MemoryTooLongDTO,
)
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_capture_turn_repository import FakeCaptureTurnRepository
from tests.fakes.fake_extraction_port import FakeExtractionPort
from tests.fakes.fake_memory_port import FakeMemoryPort
from tests.fakes.fake_pending_capture_repository import FakePendingCaptureRepository
from tests.fakes.fake_reminder_port import FakeReminderPort, fake_reminder_capture
from tests.fakes.fake_task_port import FakeTaskPort

USER = uuid.uuid4()


class Harness:
    def __init__(self, *, memory_port: FakeMemoryPort | None = None) -> None:
        self.pending = FakePendingCaptureRepository()
        self.turns = FakeCaptureTurnRepository()
        self.memory_port = memory_port or FakeMemoryPort()
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
        )
        self.answer = AnswerPendingCaptureInteractor(
            pending_capture_repository=self.pending,
            capture_turn_repository=self.turns,
            task_port=FakeTaskPort(),
            extraction=extraction,
            reminder_capture=fake_reminder_capture(extraction=extraction),
            memory_port=self.memory_port,
        )


@pytest.mark.parametrize("command", ["/remember", "/add-memory"])
async def test_both_commands_save_the_same_way(command: str) -> None:
    """C-1, FR-1."""
    harness = Harness()

    outcome = await harness.submit.submit_capture(
        user_id=USER, raw_input=f"{command} My passport expires in 2030"
    )

    assert isinstance(outcome, MemorySavedDTO)
    assert outcome.memory.text == "My passport expires in 2030"
    assert [turn.outcome for turn in harness.turns.rows] == ["memory_saved"]
    assert harness.turns.rows[0].resulting_memory_id == outcome.memory.id


async def test_an_empty_remember_asks_for_the_fact_and_the_answer_saves() -> None:
    """C-3, FR-3."""
    harness = Harness()

    question = await harness.submit.submit_capture(user_id=USER, raw_input="/remember")
    assert isinstance(question, PendingCaptureDTO)
    assert question.missing_field == "fact"
    assert question.question_text == FACT_QUESTION
    assert harness.memory_port.saved == []

    saved = await harness.answer.answer_pending_capture(
        user_id=USER, pending_capture_id=question.id, answer="Mom's birthday is Oct 12"
    )

    assert isinstance(saved, MemorySavedDTO)
    assert saved.memory.text == "Mom's birthday is Oct 12"
    assert (
        await harness.pending.get_pending_capture(
            user_id=USER, pending_capture_id=question.id
        )
        is None
    )
    assert harness.turns.rows[-1].outcome == "memory_saved"
    assert harness.turns.rows[-1].answer_text == "Mom's birthday is Oct 12"


async def test_a_refused_answer_leaves_the_question_open() -> None:
    harness = Harness()
    question = await harness.submit.submit_capture(user_id=USER, raw_input="/remember")
    assert isinstance(question, PendingCaptureDTO)
    harness.memory_port.refusal = ProviderUnavailable(message="down")

    outcome = await harness.answer.answer_pending_capture(
        user_id=USER, pending_capture_id=question.id, answer="Car renews in March"
    )

    assert isinstance(outcome, ProviderUnavailable)
    assert (
        await harness.pending.get_pending_capture(
            user_id=USER, pending_capture_id=question.id
        )
        is not None
    )


async def test_a_fact_over_500_is_a_drawn_state_not_an_error() -> None:
    """C-4, FR-4, AD-7: a 612-character fact returns MemoryTooLong."""
    harness = Harness()

    outcome = await harness.submit.submit_capture(
        user_id=USER, raw_input="/remember " + "x" * 612
    )

    assert outcome == MemoryTooLongDTO(length=612)
    assert harness.memory_port.saved == []
    assert [turn.outcome for turn in harness.turns.rows] == ["refused"]


async def test_other_commands_keep_the_500_character_line_cap() -> None:
    harness = Harness()

    with pytest.raises(ValueError):
        await harness.submit.submit_capture(
            user_id=USER, raw_input="/add-task " + "x" * 600
        )


async def test_no_line_passes_the_outer_guard() -> None:
    harness = Harness()

    with pytest.raises(ValueError):
        await harness.submit.submit_capture(
            user_id=USER, raw_input="/remember " + "x" * 1000
        )


async def test_a_model_refusal_is_passed_through_with_a_refused_turn() -> None:
    """FR-9: the same refusal a task gets, and nothing saved."""
    refusal = ProviderUnavailable(message="down")
    harness = Harness(memory_port=FakeMemoryPort(refusal=refusal))

    outcome = await harness.submit.submit_capture(
        user_id=USER, raw_input="/remember Car insurance renews every March"
    )

    assert outcome is refusal
    assert [turn.outcome for turn in harness.turns.rows] == ["refused"]


async def test_memories_lists_and_memories_with_text_looks_up() -> None:
    """FR-19, FR-20."""
    harness = Harness()
    await harness.submit.submit_capture(user_id=USER, raw_input="/remember A fact")

    listed = await harness.submit.submit_capture(user_id=USER, raw_input="/memories")
    looked_up = await harness.submit.submit_capture(
        user_id=USER, raw_input="/memories passport"
    )

    assert isinstance(listed, MemoryListDTO)
    assert [memory.text for memory in listed.memories] == ["A fact"]
    assert listed.search_text is None
    assert isinstance(looked_up, MemoryListDTO)
    assert harness.memory_port.lookups == ["passport"]
    assert [turn.outcome for turn in harness.turns.rows][-2:] == [
        "memory_listed",
        "memory_listed",
    ]


async def test_memory_is_not_a_command() -> None:
    """PRD out of scope: `/memory` falls to 001's FR-12 and suggests `/memories`."""
    harness = Harness()

    outcome = await harness.submit.submit_capture(user_id=USER, raw_input="/memory")

    assert "/memories" in getattr(outcome, "closest_matches", [])
