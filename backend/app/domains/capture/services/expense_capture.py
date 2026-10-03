"""Reads one `/add-expense` line, and each answer to its questions. Epic 006.

Shared by ``SubmitCaptureInteractor`` and ``AnswerPendingCaptureInteractor``,
so a question answered later runs the same rules as a line typed whole. This
service decides; the interactors store the question and the turn.

Order, per sub-plan 4.1 §5: the currency check runs on the raw text first, so
`$20 lunch` never costs a model call. Then one extraction call, the model's
currency, the candidate check, the description length, then ``next_step``.
Nothing is written before a save.
"""

from dataclasses import dataclass, replace
from datetime import date, datetime
from typing import Any, cast
from uuid import UUID

import structlog

from app.domains.capture.constants import (
    EXPENSE_AMOUNT_CHOICE_QUESTION,
    EXPENSE_AMOUNT_QUESTION,
    EXPENSE_AMOUNT_RETRY,
    EXPENSE_AMOUNT_TOO_LARGE,
    EXPENSE_CATEGORY_INSTRUCTION,
    EXPENSE_CATEGORY_SCHEMA,
    EXPENSE_CHIP_ANSWER_PREFIX,
    EXPENSE_DATE_PHRASE_FALLBACK,
    EXPENSE_DATE_QUESTION,
    EXPENSE_DESCRIPTION_QUESTION,
    EXPENSE_EXTRACTION_INSTRUCTION,
    EXPENSE_EXTRACTION_SCHEMA,
)
from app.domains.capture.interfaces.dtos import (
    ExpenseDraft,
    ExpenseQuestionAskedDTO,
    ExpenseQuestionKind,
    ExpenseRefusalReason,
    ExpenseRefusedDTO,
)
from app.domains.capture.interfaces.ports import (
    AnalyticsPort,
    ExpenseCaptureEventType,
    ExpensePort,
    ExtractionPort,
    LocalClockPort,
)
from app.domains.capture.services.amount_reading import (
    format_rupees,
    keep_candidates,
    names_foreign_currency,
    normalise_amount,
)
from app.domains.expenses.public import (
    MAX_AMOUNT_PAISE,
    MAX_DESCRIPTION_LENGTH,
    ExpenseCategory,
    ExpenseDTO,
    ExpenseFields,
    ExpenseSummaryDTO,
    PeriodNotUnderstood,
)
from app.domains.gateway.public import (
    Extraction,
    MalformedResult,
    ProviderTimeout,
    ProviderUnavailable,
    SharedQuotaExhausted,
    UserLimitReached,
)

logger = structlog.get_logger(__name__)

# What the model may call the rupee. Anything else is another currency (FR-6).
_RUPEE_NAMES = frozenset({"", "INR", "RS", "RS.", "₹", "RUPEE", "RUPEES"})


@dataclass(frozen=True)
class ExpenseAsk:
    """Nothing saved: ask ``kind`` about ``draft``. The interactor stores it."""

    kind: ExpenseQuestionKind
    draft: ExpenseDraft
    question: str
    date_words: str | None


@dataclass(frozen=True)
class ExpenseAnswerRejected:
    """The answer did not fit the question. It stays open, asked again."""

    question: str


ExpenseCaptureOutcome = (
    ExpenseDTO
    | ExpenseAsk
    | ExpenseRefusedDTO
    | UserLimitReached
    | ProviderUnavailable
    | ProviderTimeout
    | SharedQuotaExhausted
    | MalformedResult
)
ExpenseResumeOutcome = ExpenseCaptureOutcome | ExpenseAnswerRejected


class ExpenseCaptureService:
    def __init__(
        self,
        *,
        expense_port: ExpensePort,
        extraction: ExtractionPort,
        local_clock: LocalClockPort,
        analytics: AnalyticsPort,
    ) -> None:
        self.expense_port = expense_port
        self.extraction = extraction
        self.local_clock = local_clock
        self.analytics = analytics

    async def capture(
        self, *, user_id: UUID, argument_text: str, original_input: str
    ) -> ExpenseCaptureOutcome:
        """Read one line. A gateway failure comes back as the gateway's own
        member, unmapped, as `/add-task` returns it (FR-14)."""
        if names_foreign_currency(text=argument_text):
            return await self._refuse_currency(user_id=user_id)
        local_now, timezone_name = await self.local_clock.local_now(user_id=user_id)
        today = local_now.date()
        if not argument_text.strip():
            # Nothing to read, so no model call: ask for the amount first.
            return await self._continue(
                user_id=user_id,
                draft=ExpenseDraft(spent_on=today),
                today=today,
                original_input=original_input,
                date_words=None,
            )
        extraction_result = await self.extraction.extract(
            user_id=user_id,
            prompt=argument_text,
            schema=EXPENSE_EXTRACTION_SCHEMA,
            instruction=_extraction_instruction(
                local_now=local_now, timezone_name=timezone_name
            ),
        )
        if not isinstance(extraction_result, Extraction):
            return extraction_result
        extracted_fields = cast(dict[str, Any], extraction_result.data)
        if not _is_rupees(raw=extracted_fields.get("currency")):
            return await self._refuse_currency(user_id=user_id)
        draft = _read_draft(
            extracted_fields=extracted_fields, text=argument_text, today=today
        )
        if _is_past_ceiling(draft=draft):
            return ExpenseRefusedDTO(reason=ExpenseRefusalReason.AMOUNT_TOO_LARGE)
        if draft.description and len(draft.description) > MAX_DESCRIPTION_LENGTH:
            return ExpenseRefusedDTO(
                reason=ExpenseRefusalReason.DESCRIPTION_TOO_LONG,
                length=len(draft.description),
            )
        return await self._continue(
            user_id=user_id,
            draft=draft,
            today=today,
            original_input=original_input,
            date_words=_read_text(raw=extracted_fields.get("date_words")),
        )

    async def summarise(
        self, *, user_id: UUID, argument_text: str
    ) -> ExpenseSummaryDTO | ExpenseRefusedDTO:
        """FR-23 to FR-27: `/expenses <period>`. Expenses reads the period and
        sums; no model call and no quota."""
        outcome = await self.expense_port.summarise_text(
            user_id=user_id, text=argument_text
        )
        if isinstance(outcome, PeriodNotUnderstood):
            return ExpenseRefusedDTO(
                reason=ExpenseRefusalReason.PERIOD_NOT_UNDERSTOOD,
                period_text=outcome.text,
            )
        return outcome

    async def resume(
        self,
        *,
        user_id: UUID,
        kind: ExpenseQuestionKind,
        draft: ExpenseDraft,
        answer: str,
        original_input: str,
        date_words: str | None,
    ) -> ExpenseResumeOutcome:
        """Apply one answer, then ask the next question or save (§5)."""
        if kind == ExpenseQuestionKind.DATE:
            return await self._answer_date(
                user_id=user_id,
                draft=draft,
                answer=answer,
                original_input=original_input,
                date_words=date_words,
            )
        answered: ExpenseDraft | ExpenseRefusedDTO | ExpenseAnswerRejected
        if kind == ExpenseQuestionKind.DESCRIPTION:
            answered = await self._answer_description(
                user_id=user_id, draft=draft, answer=answer
            )
        else:
            answered = _answer_amount(kind=kind, draft=draft, answer=answer)
        if not isinstance(answered, ExpenseDraft):
            return answered
        local_now, _ = await self.local_clock.local_now(user_id=user_id)
        return await self._continue(
            user_id=user_id,
            draft=answered,
            today=local_now.date(),
            original_input=original_input,
            date_words=date_words,
        )

    async def _continue(
        self,
        *,
        user_id: UUID,
        draft: ExpenseDraft,
        today: date,
        original_input: str,
        date_words: str | None,
    ) -> ExpenseDTO | ExpenseAsk:
        step = next_step(draft=draft, today=today)
        if isinstance(step, ExpenseFields):
            return await self.expense_port.create_expense(
                user_id=user_id, fields=step, original_input=original_input
            )
        if step in (ExpenseQuestionKind.AMOUNT, ExpenseQuestionKind.AMOUNT_CHOICE):
            await self._record_event(
                user_id=user_id,
                event_type="expense_amount_asked",
                is_choice=step == ExpenseQuestionKind.AMOUNT_CHOICE,
            )
        return ExpenseAsk(
            kind=step,
            draft=draft,
            question=expense_question(kind=step, draft=draft, date_words=date_words),
            date_words=date_words,
        )

    async def _answer_date(
        self,
        *,
        user_id: UUID,
        draft: ExpenseDraft,
        answer: str,
        original_input: str,
        date_words: str | None,
    ) -> ExpenseDTO | ExpenseAnswerRejected:
        """FR-8: "Yes" and the calendar both send an ISO date, past or future.
        The date is the last question, so a confirmed date saves."""
        spent_on = _read_date(raw=answer)
        fields = _complete_fields(draft=replace(draft, spent_on=spent_on))
        if spent_on is None or fields is None:
            return ExpenseAnswerRejected(
                question=expense_question(
                    kind=ExpenseQuestionKind.DATE, draft=draft, date_words=date_words
                )
            )
        return await self.expense_port.create_expense(
            user_id=user_id, fields=fields, original_input=original_input
        )

    async def _answer_description(
        self, *, user_id: UUID, draft: ExpenseDraft, answer: str
    ) -> ExpenseDraft | ExpenseRefusedDTO:
        """FR-4. The answer is kept as typed; one call reads its category
        (build plan Q5), and any failure saves as Other (FR-10)."""
        description = answer.strip()
        if len(description) > MAX_DESCRIPTION_LENGTH:
            return ExpenseRefusedDTO(
                reason=ExpenseRefusalReason.DESCRIPTION_TOO_LONG,
                length=len(description),
            )
        category = await self._read_category(user_id=user_id, description=description)
        return replace(draft, description=description, category=category)

    async def _read_category(
        self, *, user_id: UUID, description: str
    ) -> ExpenseCategory:
        result = await self.extraction.extract(
            user_id=user_id,
            prompt=description,
            schema=EXPENSE_CATEGORY_SCHEMA,
            instruction=EXPENSE_CATEGORY_INSTRUCTION,
        )
        if not isinstance(result, Extraction):
            return ExpenseCategory.OTHER
        return _read_category(raw=cast(dict[str, Any], result.data).get("category"))

    async def _refuse_currency(self, *, user_id: UUID) -> ExpenseRefusedDTO:
        await self._record_event(
            user_id=user_id, event_type="expense_currency_refused", is_choice=False
        )
        return ExpenseRefusedDTO(reason=ExpenseRefusalReason.FOREIGN_CURRENCY)

    async def _record_event(
        self, *, user_id: UUID, event_type: ExpenseCaptureEventType, is_choice: bool
    ) -> None:
        try:
            await self.analytics.record_expense_capture_event(
                user_id=user_id, event_type=event_type, is_choice=is_choice
            )
        except Exception:
            # Broad on purpose: an instrumentation loss is logged, never raised.
            logger.exception("capture.expense_event_not_recorded", user_id=str(user_id))


def next_step(
    *, draft: ExpenseDraft, today: date
) -> ExpenseQuestionKind | ExpenseFields:
    """The next question, in build plan §5's order, or the fields to save."""
    if draft.amount_paise is None and not draft.candidates:
        return ExpenseQuestionKind.AMOUNT
    if draft.amount_paise is None:
        return ExpenseQuestionKind.AMOUNT_CHOICE
    if not draft.description:
        return ExpenseQuestionKind.DESCRIPTION
    if draft.spent_on is not None and draft.spent_on > today:
        return ExpenseQuestionKind.DATE
    fields = _complete_fields(draft=replace(draft, spent_on=draft.spent_on or today))
    assert fields is not None  # every field was checked above
    return fields


def expense_question(
    *, kind: ExpenseQuestionKind, draft: ExpenseDraft, date_words: str | None
) -> str:
    """Design §8's copy for each question."""
    if kind == ExpenseQuestionKind.AMOUNT:
        return EXPENSE_AMOUNT_QUESTION
    if kind == ExpenseQuestionKind.AMOUNT_CHOICE:
        return EXPENSE_AMOUNT_CHOICE_QUESTION
    if kind == ExpenseQuestionKind.DESCRIPTION:
        return EXPENSE_DESCRIPTION_QUESTION
    phrase = date_words.strip() if date_words else EXPENSE_DATE_PHRASE_FALLBACK
    read_date = draft.spent_on
    date_text = f"{read_date:%a} {read_date.day} {read_date:%b}" if read_date else ""
    return EXPENSE_DATE_QUESTION.format(
        phrase=phrase[:1].upper() + phrase[1:], date=date_text
    )


def expense_question_asked(
    *, pending_capture_id: UUID, ask: ExpenseAsk
) -> ExpenseQuestionAskedDTO:
    """The question card's data: chips for FR-5, the read date for FR-8."""
    return ExpenseQuestionAskedDTO(
        pending_capture_id=pending_capture_id,
        kind=ask.kind,
        question=ask.question,
        amount_candidates=ask.draft.candidates,
        read_date=(
            ask.draft.spent_on if ask.kind == ExpenseQuestionKind.DATE else None
        ),
    )


def _answer_amount(
    *, kind: ExpenseQuestionKind, draft: ExpenseDraft, answer: str
) -> ExpenseDraft | ExpenseAnswerRejected:
    """FR-3 and FR-5. A chip sends a marked candidate (dev log E-5); anything
    typed is read as rupees, as in the line itself."""
    text = answer.strip()
    chosen = chip_paise(answer=text, candidates=draft.candidates)
    if kind == ExpenseQuestionKind.AMOUNT_CHOICE and chosen is not None:
        return replace(draft, amount_paise=chosen, candidates=())
    amount_paise = normalise_amount(raw=text)
    if amount_paise is None:
        retry = (
            EXPENSE_AMOUNT_RETRY
            if kind == ExpenseQuestionKind.AMOUNT
            else EXPENSE_AMOUNT_CHOICE_QUESTION
        )
        return ExpenseAnswerRejected(question=retry)
    if amount_paise > MAX_AMOUNT_PAISE:
        return ExpenseAnswerRejected(question=EXPENSE_AMOUNT_TOO_LARGE)
    return replace(draft, amount_paise=amount_paise, candidates=())


def chip_paise(*, answer: str, candidates: tuple[int, ...]) -> int | None:
    """The candidate a chip answer names, or None for a typed answer or a
    marker that names no candidate."""
    marker, separator, digits = answer.strip().partition(EXPENSE_CHIP_ANSWER_PREFIX)
    if marker or not separator or not digits.isdigit():
        return None
    paise = int(digits)
    return paise if paise in candidates else None


def readable_answer(*, answer: str, candidates: tuple[int, ...]) -> str:
    """What the turn log keeps of an answer: a chip as the amount it shows,
    "₹180", never its marker; anything typed as typed."""
    paise = chip_paise(answer=answer, candidates=candidates)
    return answer if paise is None else format_rupees(paise=paise)


def _is_past_ceiling(*, draft: ExpenseDraft) -> bool:
    """FR-2 as amended 2026-10-03: any amount read past the storage ceiling
    refuses the line, so a typo never reaches the database (dev log E-2)."""
    amounts = (*draft.candidates, draft.amount_paise or 0)
    return any(amount > MAX_AMOUNT_PAISE for amount in amounts)


def _complete_fields(*, draft: ExpenseDraft) -> ExpenseFields | None:
    if draft.amount_paise is None or not draft.description or draft.spent_on is None:
        return None
    return ExpenseFields(
        amount_paise=draft.amount_paise,
        description=draft.description,
        # FR-10: a category never causes a question.
        category=draft.category or ExpenseCategory.OTHER,
        spent_on=draft.spent_on,
    )


def _read_draft(
    *, extracted_fields: dict[str, Any], text: str, today: date
) -> ExpenseDraft:
    raw_amounts = extracted_fields.get("amounts")
    model_amounts = (
        [str(amount) for amount in raw_amounts] if isinstance(raw_amounts, list) else []
    )
    candidates = keep_candidates(model_amounts=model_amounts, text=text)
    return ExpenseDraft(
        amount_paise=candidates[0] if len(candidates) == 1 else None,
        candidates=tuple(candidates) if len(candidates) > 1 else (),
        description=_read_description(raw=extracted_fields.get("description")),
        category=_read_category(raw=extracted_fields.get("category")),
        # FR-7: no date, or one that does not parse, is today.
        spent_on=_read_date(raw=extracted_fields.get("local_date")) or today,
    )


def _extraction_instruction(*, local_now: datetime, timezone_name: str) -> str:
    """Index §4: the user's local today, its weekday and zone."""
    return (
        f"{EXPENSE_EXTRACTION_INSTRUCTION} Today is {local_now:%A} "
        f"{local_now.date().isoformat()} in {timezone_name}."
    )


def _is_rupees(*, raw: object) -> bool:
    if raw is None:
        return True
    return isinstance(raw, str) and raw.strip().upper() in _RUPEE_NAMES


def _read_text(*, raw: object) -> str | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def _read_description(*, raw: object) -> str | None:
    """FR-4: words with no letter in them, such as "500" or "₹1,200", say
    nothing about what was bought, so they ask."""
    description = _read_text(raw=raw)
    if description is None or not any(char.isalpha() for char in description):
        return None
    return description


def _read_category(*, raw: object) -> ExpenseCategory:
    try:
        return ExpenseCategory(str(raw).strip().lower())
    except ValueError:
        return ExpenseCategory.OTHER


def _read_date(*, raw: object) -> date | None:
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw.strip()[:10])
    except ValueError:
        return None
