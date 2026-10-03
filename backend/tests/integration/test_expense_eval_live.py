"""Epic 006, sub-plan 4.1, C-21 (T-1.14): NFR-4 and NFR-5 against the real
model.

Both sets run through ``ExpenseCaptureService.capture``, the path a typed line
takes, with the real gateway and a fixed local today of Fri 2 Oct 2026, the
day both sets were written against. Nothing is saved: the expense port only
records what would have been. Runs locally, never in CI, per the `live`
marker's precedent (001's 04.3 Q4). About 113 calls.
"""

import json
import pathlib
import uuid
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_extract_interactor
from app.core.settings import Settings
from app.domains.capture.adapters.gateway_extraction_adapter import (
    GatewayExtractionAdapter,
)
from app.domains.capture.interfaces.dtos import (
    ExpenseRefusalReason,
    ExpenseRefusedDTO,
)
from app.domains.capture.services.expense_capture import (
    ExpenseAsk,
    ExpenseCaptureOutcome,
    ExpenseCaptureService,
)
from app.domains.expenses.public import ExpenseDTO
from tests.fakes.fake_analytics_port import FakeAnalyticsPort
from tests.fakes.fake_expense_port import FakeExpensePort, FakeLocalClock

EVAL_DIR = pathlib.Path(__file__).parent.parent / "eval"
CATEGORY_TARGET = 0.85
AMOUNT_TARGET = 0.98

_ASK_OUTCOMES = {
    "expense_amount": "ask_amount",
    "expense_amount_choice": "ask_amount_choice",
    "expense_description": "ask_description",
    "expense_date": "ask_date",
}


def _service(
    *, settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> ExpenseCaptureService:
    clock = FakeLocalClock()
    return ExpenseCaptureService(
        expense_port=FakeExpensePort(),
        extraction=GatewayExtractionAdapter(
            extract_interactor=build_extract_interactor(
                session_factory=session_factory, settings=settings
            ),
            local_clock=clock,
        ),
        local_clock=clock,
        analytics=FakeAnalyticsPort(),
    )


def _outcome_name(outcome: ExpenseCaptureOutcome) -> str:
    if isinstance(outcome, ExpenseDTO):
        return "save"
    if isinstance(outcome, ExpenseAsk):
        return _ASK_OUTCOMES[outcome.kind.value]
    if isinstance(outcome, ExpenseRefusedDTO):
        if outcome.reason == ExpenseRefusalReason.FOREIGN_CURRENCY:
            return "refuse_currency"
        return "refuse_too_long"
    return f"model_failure:{type(outcome).__name__}"


def _amount_case_passes(
    *, case: dict[str, Any], outcome: ExpenseCaptureOutcome
) -> bool:
    if _outcome_name(outcome) != case["expected"]:
        return False
    if isinstance(outcome, ExpenseDTO):
        return bool(outcome.amount_paise == case["amount_paise"])
    if isinstance(outcome, ExpenseAsk) and case["expected"] == "ask_amount_choice":
        return list(outcome.draft.candidates) == case["kept_candidates_paise"]
    return True


@pytest.mark.live
async def test_amount_reading_meets_nfr_5(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    eval_user: uuid.UUID,
) -> None:
    service = _service(settings=settings, session_factory=session_factory)
    cases = json.loads((EVAL_DIR / "expense_amounts.json").read_text())["cases"]
    misses: list[str] = []
    for case in cases:
        argument_text = case["input"].removeprefix("/add-expense").strip()
        outcome = await service.capture(
            user_id=eval_user, argument_text=argument_text, original_input=case["input"]
        )
        if not _amount_case_passes(case=case, outcome=outcome):
            got = _outcome_name(outcome)
            if isinstance(outcome, ExpenseDTO):
                got += f" {outcome.amount_paise}"
            if isinstance(outcome, ExpenseAsk):
                got += f" {list(outcome.draft.candidates)}"
            misses.append(f"{case['input']!r}: expected {case['expected']}, got {got}")

    accuracy = 1 - len(misses) / len(cases)
    print(f"NFR-5 accuracy {accuracy:.1%} over {len(cases)} cases")
    for miss in misses:
        print("  miss:", miss)
    assert accuracy > AMOUNT_TARGET


@pytest.mark.live
async def test_category_accuracy_meets_nfr_4(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    eval_user: uuid.UUID,
) -> None:
    service = _service(settings=settings, session_factory=session_factory)
    cases = json.loads((EVAL_DIR / "expense_categories.json").read_text())["cases"]
    misses: list[str] = []
    for case in cases:
        # A fixed, unambiguous amount, so only the category is being scored.
        argument_text = f"₹500 {case['description']}"
        outcome = await service.capture(
            user_id=eval_user,
            argument_text=argument_text,
            original_input=f"/add-expense {argument_text}",
        )
        if isinstance(outcome, ExpenseDTO):
            got = outcome.category.value
        elif isinstance(outcome, ExpenseAsk) and outcome.draft.category:
            got = outcome.draft.category.value
        else:
            got = _outcome_name(outcome)
        if got != case["expected"]:
            misses.append(
                f"{case['description']!r}: expected {case['expected']}, got {got}"
            )

    accuracy = 1 - len(misses) / len(cases)
    print(f"NFR-4 accuracy {accuracy:.1%} over {len(cases)} cases")
    for miss in misses:
        print("  miss:", miss)
    assert accuracy > CATEGORY_TARGET
