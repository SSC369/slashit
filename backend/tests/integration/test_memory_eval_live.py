"""NFR-6, sub-plan 4.1 case C-15: category accuracy against the real model.

Scores ``tests/eval/memory_categories.json`` through the same judgement call a
save makes. Spends a fraction of a cent per case. Runs locally, never in CI,
per the `live` marker's precedent (04.3 Q4).
"""

import json
import pathlib
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_embed_interactor, build_extract_interactor
from app.core.settings import Settings
from app.domains.memories.adapters.gateway_adapter import GatewayMemoryModelAdapter
from app.domains.memories.interfaces.dtos import CategoryJudgement

EVAL_SET = pathlib.Path(__file__).parent.parent / "eval" / "memory_categories.json"
TARGET_ACCURACY = 0.85


@pytest.mark.live
async def test_category_accuracy_meets_nfr_6(
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
    cases = json.loads(EVAL_SET.read_text())["cases"]
    misses: list[str] = []
    for case in cases:
        judgement = await adapter.judge_fact(
            user_id=user_id, text=case["fact"], candidates=[]
        )
        assert isinstance(judgement, CategoryJudgement), judgement
        got = judgement.category.value if judgement.category else None
        if got != case["expected"]:
            misses.append(f"{case['fact']!r}: expected {case['expected']}, got {got}")

    accuracy = 1 - len(misses) / len(cases)
    print(f"NFR-6 accuracy {accuracy:.0%} over {len(cases)} cases")
    for miss in misses:
        print("  miss:", miss)
    assert accuracy > TARGET_ACCURACY
