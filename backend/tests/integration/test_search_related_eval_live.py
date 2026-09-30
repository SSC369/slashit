"""NFR-9, sub-plan 4.3 case C-3.13: related lists against real vectors, and
the evidence for tuning RELATED_MAX_DISTANCE (AD-6).

Seeds ``search_queries.json``'s records with real embeddings, as C-15 does,
then lists each case's related records. Scores the list against
``related_records.json``'s labels as a stand-in for the hand judgement
NFR-9 names, and prints every listed record with its distance, labelled or
not, for that judgement and for choosing the threshold. Runs locally, never
in CI (`live`).
"""

import json
import pathlib
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.deps import build_search_service
from app.core.settings import Settings
from app.domains.search.constants import RELATED_MAX_DISTANCE
from app.domains.search.interfaces.dtos import RecordType
from tests.integration.test_search_eval_live import EVAL_SET, _JobContext, _seed

RELATED_SET = pathlib.Path(__file__).parent.parent / "eval" / "related_records.json"
TARGET_PRECISION = 0.70
_TYPES = {"t": RecordType.TASK, "r": RecordType.REMINDER, "m": RecordType.MEMORY}


@pytest.mark.live
async def test_related_lists_meet_nfr_9(
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
    ids = {key: record_id for record_id, key in keys.items()}

    listed = 0
    labelled = 0
    empty_lists: list[str] = []
    for case in json.loads(RELATED_SET.read_text())["cases"]:
        async with session_factory() as session:
            service = build_search_service(
                _JobContext(session=session, session_factory=session_factory)  # type: ignore[arg-type]
            )
            related = await service.related(
                user_id=user_id,
                record_type=_TYPES[case["record"][0]],
                record_id=ids[case["record"]],
            )
        print(f"\n{case['record']}: {texts[case['record']]}")
        if not related:
            empty_lists.append(case["record"])
        for record in related:
            key = keys[record.item.id]
            is_labelled = key in case["related"]
            listed += 1
            labelled += is_labelled
            print(f"  {'+' if is_labelled else '?'} {key}: {texts[key]}")

    precision = labelled / listed if listed else 0.0
    print(
        f"\nNFR-9 at RELATED_MAX_DISTANCE {RELATED_MAX_DISTANCE}: {listed} listed, "
        f"{precision:.0%} labelled related. '?' rows need a hand judgement"
    )
    print(f"Records with nothing related: {empty_lists}")
    assert precision > TARGET_PRECISION
