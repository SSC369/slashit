"""NFR-7, sub-plan 4.3 case C-3.13: conflict accuracy against the real model.

Scores ``tests/eval/memory_conflicts.json`` through the same judgement call a
save makes, with each case's ten candidates offered as the candidate search
would offer them. Runs locally, never in CI, per the `live` marker.
"""

import json
import pathlib
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_embed_interactor, build_extract_interactor
from app.core.settings import Settings
from app.domains.memories.adapters.gateway_adapter import GatewayMemoryModelAdapter
from app.domains.memories.interfaces.dtos import CandidateMemory, CategoryJudgement

EVAL_SET = pathlib.Path(__file__).parent.parent / "eval" / "memory_conflicts.json"
TARGET_CAUGHT = 0.80
TARGET_FALSE_FLAGS = 0.10
MAX_TRAP_CASES_FLAGGED = 1


@pytest.mark.live
async def test_conflict_check_meets_nfr_7(
    settings: Settings,
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    user_id, _ = two_users
    adapter = GatewayMemoryModelAdapter(
        embed_interactor=build_embed_interactor(
            session_factory=session_factory, settings=settings
        ),
        extract_interactor=build_extract_interactor(
            session_factory=session_factory, settings=settings
        ),
    )
    eval_set = json.loads(EVAL_SET.read_text())
    bank: dict[str, str] = eval_set["bank"]
    caught = contradicting_pairs = false_flags = other_pairs = 0
    trap_cases_flagged: list[str] = []
    misses: list[str] = []
    for case in eval_set["cases"]:
        ids = {bank_id: uuid.uuid4() for bank_id in case["candidates"]}
        judgement = await adapter.judge_fact(
            user_id=user_id,
            text=case["fact"],
            candidates=[
                CandidateMemory(id=memory_id, text=bank[bank_id])
                for bank_id, memory_id in ids.items()
            ],
        )
        assert isinstance(judgement, CategoryJudgement), judgement
        flagged = {
            bank_id
            for bank_id, memory_id in ids.items()
            if memory_id in judgement.conflicting_ids
        }
        expected = set(case["expected_conflicts"])
        caught += len(flagged & expected)
        contradicting_pairs += len(expected)
        false_flags += len(flagged - expected)
        other_pairs += len(ids) - len(expected)
        if case["kind"] == "trap" and flagged - expected:
            trap_cases_flagged.append(case["id"])
        if flagged != expected:
            misses.append(
                f"{case['id']} expected {sorted(expected)}, got {sorted(flagged)}"
            )

    caught_rate = caught / contradicting_pairs
    false_flag_rate = false_flags / other_pairs
    print(f"NFR-7 caught {caught_rate:.0%} of {contradicting_pairs} contradictions")
    print(f"NFR-7 flagged {false_flag_rate:.1%} of {other_pairs} other pairs")
    print(f"Trap cases flagged: {trap_cases_flagged}")
    for miss in misses:
        print("  miss:", miss)
    assert caught_rate > TARGET_CAUGHT
    assert false_flag_rate < TARGET_FALSE_FLAGS
    assert len(trap_cases_flagged) <= MAX_TRAP_CASES_FLAGGED
