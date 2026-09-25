"""Capture's `/forget`, sub-plan 4.2 case C-2.8 and FR-28."""

import uuid

from app.domains.capture.interactors.confirm_forget import ConfirmForgetInteractor
from app.domains.capture.interactors.submit_capture import SubmitCaptureInteractor
from app.domains.memories.public import (
    ForgetCandidatesDTO,
    MemoriesForgottenDTO,
    MemoryCountChangedDTO,
)
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_capture_turn_repository import FakeCaptureTurnRepository
from tests.fakes.fake_extraction_port import FakeExtractionPort
from tests.fakes.fake_memory_port import FakeMemoryPort
from tests.fakes.fake_pending_capture_repository import FakePendingCaptureRepository
from tests.fakes.fake_reminder_port import FakeReminderPort, fake_reminder_capture
from tests.fakes.fake_task_port import FakeTaskPort

USER = uuid.uuid4()


def _harness() -> tuple[
    SubmitCaptureInteractor,
    ConfirmForgetInteractor,
    FakeCaptureTurnRepository,
    FakeMemoryPort,
]:
    turns = FakeCaptureTurnRepository()
    memory_port = FakeMemoryPort()
    extraction = FakeExtractionPort()
    submit = SubmitCaptureInteractor(
        pending_capture_repository=FakePendingCaptureRepository(),
        capture_turn_repository=turns,
        task_port=FakeTaskPort(),
        extraction=extraction,
        analytics=FakeAnalyticsPort(),
        reminder_port=FakeReminderPort(),
        reminder_capture=fake_reminder_capture(extraction=extraction),
        memory_port=memory_port,
    )
    confirm = ConfirmForgetInteractor(
        memory_port=memory_port, capture_turn_repository=turns
    )
    return submit, confirm, turns, memory_port


async def test_forget_offers_candidates_and_writes_no_turn() -> None:
    """FR-28: the words typed after /forget are never stored."""
    submit, _, turns, _ = _harness()
    await submit.submit_capture(user_id=USER, raw_input="/remember My passport number")
    turns.rows.clear()

    offered = await submit.submit_capture(
        user_id=USER, raw_input="/forget my passport number"
    )

    assert isinstance(offered, ForgetCandidatesDTO)
    assert len(offered.candidates) == 1
    assert turns.rows == []


async def test_a_bare_forget_offers_nothing_with_empty_search_text() -> None:
    """Sub-plan 4.2 §6: the card explains how to use it."""
    submit, _, turns, _ = _harness()

    offered = await submit.submit_capture(user_id=USER, raw_input="/forget")

    assert isinstance(offered, ForgetCandidatesDTO)
    assert offered.search_text == ""
    assert offered.candidates == []
    assert turns.rows == []


async def test_a_confirmed_forget_records_only_the_command_and_count() -> None:
    """C-2.8."""
    submit, confirm, turns, memory_port = _harness()
    await submit.submit_capture(user_id=USER, raw_input="/remember Fact one")
    await submit.submit_capture(user_id=USER, raw_input="/remember Fact two")
    ids = [memory.id for memory in memory_port.saved]
    turns.rows.clear()

    outcome = await confirm.confirm_forget(
        user_id=USER, memory_ids=ids, forget_all=False, expected_count=0
    )

    assert outcome == MemoriesForgottenDTO(count=2)
    assert [
        (turn.input_text, turn.outcome, turn.affected_count) for turn in turns.rows
    ] == [("/forget", "memory_forgotten", 2)]


async def test_nothing_forgotten_writes_no_turn() -> None:
    _, confirm, turns, _ = _harness()

    outcome = await confirm.confirm_forget(
        user_id=USER, memory_ids=[uuid.uuid4()], forget_all=False, expected_count=0
    )

    assert outcome == MemoriesForgottenDTO(count=0)
    assert turns.rows == []


async def test_a_stale_forget_all_changes_nothing() -> None:
    submit, confirm, turns, memory_port = _harness()
    await submit.submit_capture(user_id=USER, raw_input="/remember Fact one")
    turns.rows.clear()

    outcome = await confirm.confirm_forget(
        user_id=USER, memory_ids=[], forget_all=True, expected_count=5
    )

    assert outcome == MemoryCountChangedDTO(count=1)
    assert len(memory_port.saved) == 1
    assert turns.rows == []
