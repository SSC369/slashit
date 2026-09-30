"""NFR-8, sub-plan 4.2 case C-2.13: written answers against the real model.

Seeds ``search_queries.json``'s records for one user, as C-15 does, then asks
every question in ``search_answers.json`` through the whole search. Asserts
what a machine can judge: no sentence without a citation, and a no-support
reply for the questions nothing answers. Prints each answer beside the
records it cites, for the hand judgement NFR-8's second half needs. Runs
locally, never in CI (`live`).
"""

import json
import pathlib
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_search_service
from app.core.settings import Settings
from tests.integration.test_search_eval_live import EVAL_SET, _JobContext, _seed

ANSWER_SET = pathlib.Path(__file__).parent.parent / "eval" / "search_answers.json"
# `estimate`: the PRD sets no rate for FR-18; two of eight is the line at
# which the no-support rule is judged not to hold.
UNANSWERABLE_MISSES_ALLOWED = 2


@pytest.mark.live
async def test_answers_are_grounded_per_nfr_8(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    eval_user: uuid.UUID,
) -> None:
    user_id = eval_user
    records = json.loads(EVAL_SET.read_text())["records"]
    texts = {record["key"]: record["text"] for record in records}
    keys = await _seed(
        session_factory=session_factory,
        settings=settings,
        user_id=user_id,
        records=records,
    )

    uncited_sentences = 0
    answered_unanswerable: list[str] = []
    missed_answerable: list[str] = []
    for case in json.loads(ANSWER_SET.read_text())["cases"]:
        async with session_factory() as session:
            service = build_search_service(
                _JobContext(session=session, session_factory=session_factory)  # type: ignore[arg-type]
            )
            results = await service.search_for_capture(
                user_id=user_id, text=case["question"]
            )
        assert not results.answer_unavailable, case["question"]
        cited = {
            hit.citation: keys[hit.item.id]
            for group in results.groups
            for hit in group.hits
            if hit.citation is not None
        }
        print(f"\nQ: {case['question']}  (expected {case['cites'] or 'no support'})")
        if results.answer is None:
            print("  no support")
            if case["cites"]:
                missed_answerable.append(case["question"])
            continue
        if not case["cites"]:
            answered_unanswerable.append(case["question"])
        for sentence in results.answer.sentences:
            uncited_sentences += not sentence.citations
            print(f"  {sentence.text} {sentence.citations}")
            for citation in sentence.citations:
                print(f"    [{citation}] {cited[citation]}: {texts[cited[citation]]}")

    print(f"\nNFR-8 uncited sentences: {uncited_sentences}")
    print(f"Unanswerable questions answered anyway: {answered_unanswerable}")
    print(f"Answerable questions given no support: {missed_answerable}")
    assert uncited_sentences == 0
    assert len(answered_unanswerable) <= UNANSWERABLE_MISSES_ALLOWED
