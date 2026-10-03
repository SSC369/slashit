"""Epic 006, sub-plan 4.1 §7: C-4 to C-13. `/add-expense` and its questions,
through capture's two interactors, against fakes."""

import uuid
from datetime import date
from typing import Any, cast

import pytest
from strawberry.scalars import JSON

from app.domains.capture.interactors.answer_pending_capture import (
    AnswerPendingCaptureInteractor,
)
from app.domains.capture.interactors.submit_capture import SubmitCaptureInteractor
from app.domains.capture.interfaces.dtos import (
    ExpenseQuestionAskedDTO,
    ExpenseQuestionKind,
    ExpenseRefusalReason,
    ExpenseRefusedDTO,
)
from app.domains.capture.services.expense_capture import ExpenseCaptureService
from app.domains.expenses.public import ExpenseCategory, ExpenseDTO, ExpenseSummaryDTO
from app.domains.gateway.public import Extraction, ExtractionResult, ProviderUnavailable
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_capture_turn_repository import FakeCaptureTurnRepository
from tests.fakes.fake_event_ports import FakeEventPort, fake_event_capture
from tests.fakes.fake_expense_port import TODAY, FakeExpensePort, FakeLocalClock
from tests.fakes.fake_extraction_port import FakeExtractionPort
from tests.fakes.fake_memory_port import FakeMemoryPort
from tests.fakes.fake_pending_capture_repository import FakePendingCaptureRepository
from tests.fakes.fake_reminder_port import FakeReminderPort, fake_reminder_capture
from tests.fakes.fake_search_port import FakeSearchPort
from tests.fakes.fake_task_port import FakeTaskPort

USER = uuid.uuid4()


def read(**fields: Any) -> Extraction:
    """What the model returned for one call."""
    return Extraction(
        data=cast(JSON, fields), model="fake", input_tokens=1, output_tokens=1
    )


def line(
    *,
    amounts: list[str],
    description: str = "",
    category: str = "food",
    currency: str | None = None,
    local_date: str | None = None,
    date_words: str | None = None,
) -> Extraction:
    fields: dict[str, Any] = {
        "amounts": amounts,
        "description": description,
        "category": category,
    }
    if currency is not None:
        fields["currency"] = currency
    if local_date is not None:
        fields["local_date"] = local_date
    if date_words is not None:
        fields["date_words"] = date_words
    return read(**fields)


class Harness:
    def __init__(self, *, results: list[ExtractionResult] | None = None) -> None:
        self.turns = FakeCaptureTurnRepository()
        self.pending = FakePendingCaptureRepository()
        self.expenses = FakeExpensePort()
        self.analytics = FakeAnalyticsPort()
        self.extraction = FakeExtractionPort(results=results or [])
        expense_capture = ExpenseCaptureService(
            expense_port=self.expenses,
            extraction=self.extraction,
            local_clock=FakeLocalClock(),
            analytics=self.analytics,
        )
        self.submit = SubmitCaptureInteractor(
            pending_capture_repository=self.pending,
            capture_turn_repository=self.turns,
            task_port=FakeTaskPort(),
            extraction=self.extraction,
            analytics=self.analytics,
            reminder_port=FakeReminderPort(),
            reminder_capture=fake_reminder_capture(extraction=self.extraction),
            memory_port=FakeMemoryPort(),
            search_port=FakeSearchPort(),
            event_port=FakeEventPort(),
            event_capture=fake_event_capture(extraction=self.extraction),
            expense_capture=expense_capture,
        )
        self.answer = AnswerPendingCaptureInteractor(
            pending_capture_repository=self.pending,
            capture_turn_repository=self.turns,
            task_port=FakeTaskPort(),
            extraction=self.extraction,
            reminder_capture=fake_reminder_capture(extraction=self.extraction),
            memory_port=FakeMemoryPort(),
            search_port=FakeSearchPort(),
            event_capture=fake_event_capture(extraction=self.extraction),
            expense_capture=expense_capture,
        )

    async def type_line(self, text: str) -> object:
        return await self.submit.submit_capture(user_id=USER, raw_input=text)

    async def reply(self, question: object, answer: str) -> object:
        assert isinstance(question, ExpenseQuestionAskedDTO)
        return await self.answer.answer_pending_capture(
            user_id=USER, pending_capture_id=question.pending_capture_id, answer=answer
        )


async def test_a_whole_line_saves_with_every_field() -> None:
    """FR-1, FR-7, FR-12: amount, description, category and a past date."""
    harness = Harness(
        results=[
            line(
                amounts=["850"],
                description="dinner with friends",
                local_date="2026-10-01",
                date_words="yesterday",
            )
        ]
    )

    saved = await harness.type_line("/add-expense ₹850 dinner with friends yesterday")

    assert isinstance(saved, ExpenseDTO)
    assert saved.amount_paise == 85_000
    assert saved.category == ExpenseCategory.FOOD
    assert saved.spent_on == date(2026, 10, 1)
    assert [turn.outcome for turn in harness.turns.rows] == ["expense_saved"]
    assert harness.turns.rows[0].resulting_expense_id == saved.id
    assert harness.pending.rows == {}


async def test_another_currency_refuses_without_a_model_call() -> None:
    """C-4, FR-6: `$20 lunch` costs no request."""
    harness = Harness()

    refused = await harness.type_line("/add-expense $20 lunch")

    assert refused == ExpenseRefusedDTO(reason=ExpenseRefusalReason.FOREIGN_CURRENCY)
    assert harness.extraction.calls == []
    assert [turn.outcome for turn in harness.turns.rows] == ["refused"]
    assert harness.expenses.saved == []
    assert harness.analytics.expense_capture_events == [
        ("expense_currency_refused", False)
    ]


async def test_a_currency_the_model_names_refuses() -> None:
    """C-5, FR-6, AD-8: the model's currency is the second check."""
    harness = Harness(
        results=[line(amounts=["20"], description="lunch", currency="USD")]
    )

    refused = await harness.type_line("/add-expense 20 lunch")

    assert isinstance(refused, ExpenseRefusedDTO)
    assert refused.reason == ExpenseRefusalReason.FOREIGN_CURRENCY
    assert harness.expenses.saved == []


@pytest.mark.parametrize("currency", ["INR", "inr", "₹", "Rs", ""])
async def test_the_rupee_by_any_name_is_not_another_currency(currency: str) -> None:
    harness = Harness(
        results=[line(amounts=["20"], description="tea", currency=currency)]
    )

    assert isinstance(await harness.type_line("/add-expense 20 tea"), ExpenseDTO)


async def test_no_amount_asks_and_the_answer_saves() -> None:
    """C-6, FR-3."""
    harness = Harness(results=[line(amounts=[], description="dinner")])

    question = await harness.type_line("/add-expense dinner")

    assert isinstance(question, ExpenseQuestionAskedDTO)
    assert question.kind == ExpenseQuestionKind.AMOUNT
    assert question.question == "How much was it?"
    assert harness.expenses.saved == []
    assert harness.analytics.expense_capture_events == [("expense_amount_asked", False)]

    saved = await harness.reply(question, "850")

    assert isinstance(saved, ExpenseDTO)
    assert saved.amount_paise == 85_000
    assert saved.description == "dinner"
    assert harness.pending.rows == {}
    assert harness.turns.rows[-1].outcome == "expense_saved"
    assert harness.turns.rows[-1].answer_text == "850"


async def test_an_amount_answer_that_is_not_an_amount_asks_again() -> None:
    """§5: the same question, with an example, and the row kept."""
    harness = Harness(results=[line(amounts=[], description="dinner")])
    question = await harness.type_line("/add-expense dinner")

    again = await harness.reply(question, "a lot")

    assert isinstance(again, ExpenseQuestionAskedDTO)
    assert isinstance(question, ExpenseQuestionAskedDTO)
    assert again.pending_capture_id == question.pending_capture_id
    assert again.question == "Enter an amount such as 850 or 1,200.50"
    assert harness.expenses.saved == []


async def test_an_amount_answer_past_the_ceiling_asks_again() -> None:
    """FR-2 as amended 2026-10-03 (dev log E-2): the question stays open with
    the too-large copy, and nothing reaches the database."""
    harness = Harness(results=[line(amounts=[], description="dinner")])
    question = await harness.type_line("/add-expense dinner")

    again = await harness.reply(question, "1" + "0" * 20)

    assert isinstance(again, ExpenseQuestionAskedDTO)
    assert again.question == (
        "That amount is too large to save. Check it for an extra zero."
    )
    assert harness.expenses.saved == []


async def test_no_description_asks_and_a_second_call_reads_the_category() -> None:
    """C-7, FR-4, build plan Q5."""
    harness = Harness(
        results=[
            line(amounts=["500"], description="", category="other"),
            read(category="food"),
        ]
    )

    question = await harness.type_line("/add-expense 500")

    assert isinstance(question, ExpenseQuestionAskedDTO)
    assert question.kind == ExpenseQuestionKind.DESCRIPTION
    assert question.question == "What was the expense for?"

    saved = await harness.reply(question, "  snacks ")

    assert isinstance(saved, ExpenseDTO)
    assert saved.description == "snacks"
    assert saved.category == ExpenseCategory.FOOD
    assert harness.extraction.calls == ["500", "snacks"]


async def test_a_late_description_saves_as_other_when_the_model_fails() -> None:
    """FR-10: a category never causes a question or a refusal."""
    harness = Harness(
        results=[
            line(amounts=["500"]),
            ProviderUnavailable(message="down"),
        ]
    )
    question = await harness.type_line("/add-expense 500")

    saved = await harness.reply(question, "snacks")

    assert isinstance(saved, ExpenseDTO)
    assert saved.category == ExpenseCategory.OTHER


async def test_two_numbers_ask_which_and_the_chip_saves_it() -> None:
    """C-8, FR-5: one chip per number, sent back as a marked candidate (dev
    log E-5). The history keeps the amount the chip showed."""
    harness = Harness(results=[line(amounts=["2", "180"], description="2 coffees")])

    question = await harness.type_line("/add-expense 2 coffees 180")

    assert isinstance(question, ExpenseQuestionAskedDTO)
    assert question.kind == ExpenseQuestionKind.AMOUNT_CHOICE
    assert question.amount_candidates == (200, 18_000)
    assert harness.analytics.expense_capture_events == [("expense_amount_asked", True)]

    saved = await harness.reply(question, "chip:18000")

    assert isinstance(saved, ExpenseDTO)
    assert saved.amount_paise == 18_000
    assert saved.description == "2 coffees"
    assert harness.turns.rows[-1].answer_text == "₹180"


async def test_typed_digits_equal_to_a_candidates_paise_are_rupees() -> None:
    """Dev log E-5: "18000" typed is ₹18,000, never the ₹180 chip, whose paise
    happen to be the same digits."""
    harness = Harness(results=[line(amounts=["2", "180"], description="2 coffees")])
    question = await harness.type_line("/add-expense 2 coffees 180")

    saved = await harness.reply(question, "18000")

    assert isinstance(saved, ExpenseDTO)
    assert saved.amount_paise == 1_800_000


async def test_a_marker_that_names_no_candidate_is_not_a_chip() -> None:
    harness = Harness(results=[line(amounts=["2", "180"], description="2 coffees")])
    question = await harness.type_line("/add-expense 2 coffees 180")

    again = await harness.reply(question, "chip:999")

    assert isinstance(again, ExpenseQuestionAskedDTO)
    assert harness.expenses.saved == []


async def test_a_typed_answer_to_the_choice_is_read_as_rupees() -> None:
    harness = Harness(results=[line(amounts=["2", "180"], description="2 coffees")])
    question = await harness.type_line("/add-expense 2 coffees 180")

    saved = await harness.reply(question, "₹180")

    assert isinstance(saved, ExpenseDTO)
    assert saved.amount_paise == 18_000


async def test_a_future_date_asks_and_the_read_date_saves() -> None:
    """C-9, FR-8: confirmed with "Yes"."""
    harness = Harness(
        results=[
            line(
                amounts=["1,200"],
                description="concert tickets",
                category="entertainment",
                local_date="2026-10-10",
                date_words="next Saturday",
            )
        ]
    )

    question = await harness.type_line(
        "/add-expense ₹1,200 concert tickets next Saturday"
    )

    assert isinstance(question, ExpenseQuestionAskedDTO)
    assert question.kind == ExpenseQuestionKind.DATE
    assert question.read_date == date(2026, 10, 10)
    assert question.question == (
        "Next Saturday reads as Sat 10 Oct, which is after today. "
        "Save it for that date?"
    )
    assert harness.expenses.saved == []

    saved = await harness.reply(question, "2026-10-10")

    assert isinstance(saved, ExpenseDTO)
    assert saved.spent_on == date(2026, 10, 10)


async def test_a_date_picked_from_the_calendar_saves_that_date() -> None:
    """C-9: past or future, any date the calendar sends."""
    harness = Harness(
        results=[
            line(
                amounts=["1200"],
                description="concert tickets",
                local_date="2026-10-10",
            )
        ]
    )
    question = await harness.type_line("/add-expense 1200 concert tickets sat")

    saved = await harness.reply(question, "2026-10-03")

    assert isinstance(saved, ExpenseDTO)
    assert saved.spent_on == date(2026, 10, 3)


async def test_a_date_answer_that_is_not_a_date_asks_again() -> None:
    harness = Harness(
        results=[line(amounts=["1200"], description="gig", local_date="2026-10-10")]
    )
    question = await harness.type_line("/add-expense 1200 gig")

    again = await harness.reply(question, "soon")

    assert isinstance(again, ExpenseQuestionAskedDTO)
    assert again.kind == ExpenseQuestionKind.DATE
    assert again.read_date == date(2026, 10, 10)
    assert harness.expenses.saved == []


async def test_today_or_earlier_saves_without_asking() -> None:
    harness = Harness(
        results=[line(amounts=["90"], description="tea", local_date=TODAY.isoformat())]
    )

    assert isinstance(await harness.type_line("/add-expense 90 tea"), ExpenseDTO)


async def test_missing_amount_and_description_ask_twice_in_order() -> None:
    """C-10, FR-15, §5: each answer replaces the question it answers."""
    harness = Harness(results=[line(amounts=[], description=""), read(category="food")])

    first = await harness.type_line("/add-expense dinner")
    assert isinstance(first, ExpenseQuestionAskedDTO)
    assert first.kind == ExpenseQuestionKind.AMOUNT

    second = await harness.reply(first, "500")

    assert isinstance(second, ExpenseQuestionAskedDTO)
    assert second.kind == ExpenseQuestionKind.DESCRIPTION
    assert list(harness.pending.rows) == [second.pending_capture_id]
    assert harness.expenses.saved == []

    saved = await harness.reply(second, "dinner")

    assert isinstance(saved, ExpenseDTO)
    assert saved.amount_paise == 50_000
    assert harness.pending.rows == {}
    assert [turn.outcome for turn in harness.turns.rows] == [
        "question_asked",
        "question_asked",
        "expense_saved",
    ]


async def test_a_bare_command_asks_for_the_amount_without_a_model_call() -> None:
    harness = Harness()

    question = await harness.type_line("/add-expense")

    assert isinstance(question, ExpenseQuestionAskedDTO)
    assert question.kind == ExpenseQuestionKind.AMOUNT
    assert harness.extraction.calls == []


async def test_a_description_of_201_characters_refuses_and_200_saves() -> None:
    """C-11, FR-13."""
    too_long = Harness(results=[line(amounts=["450"], description="d" * 201)])

    refused = await too_long.type_line("/add-expense 450 " + "d" * 201)

    assert refused == ExpenseRefusedDTO(
        reason=ExpenseRefusalReason.DESCRIPTION_TOO_LONG, length=201
    )
    assert too_long.expenses.saved == []
    assert [turn.outcome for turn in too_long.turns.rows] == ["refused"]

    at_limit = Harness(results=[line(amounts=["450"], description="d" * 200)])
    assert isinstance(
        await at_limit.type_line("/add-expense 450 " + "d" * 200), ExpenseDTO
    )


async def test_an_over_long_description_answer_keeps_the_question_open() -> None:
    harness = Harness(results=[line(amounts=["500"])])
    question = await harness.type_line("/add-expense 500")

    refused = await harness.reply(question, "d" * 201)

    assert isinstance(refused, ExpenseRefusedDTO)
    assert refused.length == 201
    assert isinstance(question, ExpenseQuestionAskedDTO)
    assert question.pending_capture_id in harness.pending.rows


async def test_a_gateway_failure_passes_through_with_nothing_saved() -> None:
    """C-12, FR-14."""
    failure = ProviderUnavailable(message="down")
    harness = Harness(results=[failure])

    outcome = await harness.type_line("/add-expense ₹640 pharmacy")

    assert outcome is failure
    assert harness.expenses.saved == []
    assert harness.pending.rows == {}
    assert [turn.outcome for turn in harness.turns.rows] == ["refused"]


async def test_the_description_is_the_models_trimmed_and_the_line_is_kept() -> None:
    """C-13, FR-11."""
    harness = Harness(results=[line(amounts=["320"], description="  Uber to office ")])

    saved = await harness.type_line("  /add-expense Uber to office 320  ")

    assert isinstance(saved, ExpenseDTO)
    assert saved.description == "Uber to office"
    assert harness.expenses.original_inputs == ["/add-expense Uber to office 320"]


async def test_a_number_the_model_invents_is_dropped_and_asks() -> None:
    """FR-3, AD-4: zero kept candidates asks for the amount."""
    harness = Harness(results=[line(amounts=["900"], description="dinner")])

    question = await harness.type_line("/add-expense dinner 850 ish")

    assert isinstance(question, ExpenseQuestionAskedDTO)
    assert question.kind == ExpenseQuestionKind.AMOUNT


@pytest.mark.parametrize(
    ("category", "local_date", "expected_category", "expected_date"),
    [
        ("groceries", None, ExpenseCategory.OTHER, TODAY),
        ("travel", "last tuesday", ExpenseCategory.TRAVEL, TODAY),
    ],
)
async def test_unreadable_category_and_date_fall_back(
    category: str,
    local_date: str | None,
    expected_category: ExpenseCategory,
    expected_date: date,
) -> None:
    """§6: an unknown category is Other; an unparseable date is today."""
    harness = Harness(
        results=[
            line(
                amounts=["300"],
                description="stuff",
                category=category,
                local_date=local_date,
            )
        ]
    )

    saved = await harness.type_line("/add-expense 300 stuff")

    assert isinstance(saved, ExpenseDTO)
    assert saved.category == expected_category
    assert saved.spent_on == expected_date


# --- Sub-plan 4.2: `/expenses` ---


async def test_expenses_sums_the_period_without_a_model_call() -> None:
    """C-32, FR-23: no model call, no quota, one `expenses_summarised` turn."""
    harness = Harness(
        results=[
            line(amounts=["850"], description="dinner", local_date="2026-10-01"),
        ]
    )
    await harness.type_line("/add-expense ₹850 dinner yesterday")
    calls_before = len(harness.extraction.calls)

    summary = await harness.type_line("/expenses this month")

    assert isinstance(summary, ExpenseSummaryDTO)
    assert (summary.label, summary.grand_total_paise, summary.count) == (
        "October 2026 so far",
        85_000,
        1,
    )
    assert len(harness.extraction.calls) == calls_before
    assert [turn.outcome for turn in harness.turns.rows][-1] == "expenses_summarised"


async def test_expenses_with_no_period_reads_this_month() -> None:
    """FR-24."""
    harness = Harness()

    summary = await harness.type_line("/expenses")

    assert isinstance(summary, ExpenseSummaryDTO)
    assert summary.label == "October 2026 so far"
    assert harness.expenses.summarised_texts == [""]


async def test_a_period_off_the_list_refuses_and_quotes_it() -> None:
    """FR-27."""
    harness = Harness()

    refused = await harness.type_line("/expenses since diwali")

    assert refused == ExpenseRefusedDTO(
        reason=ExpenseRefusalReason.PERIOD_NOT_UNDERSTOOD, period_text="since diwali"
    )
    assert harness.extraction.calls == []
    assert [turn.outcome for turn in harness.turns.rows] == ["refused"]
