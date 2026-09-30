"""Epic 005, sub-plan 4.1, C-1 and C-2: ranking tiers and grouping (AD-3,
FR-6 to FR-8)."""

import uuid
from datetime import UTC, datetime

from app.domains.records.public import TaskDTO
from app.domains.search.interfaces.dtos import RecordType, SearchCandidate
from app.domains.search.services.ranking import group_hits, rank_key

NOW = datetime(2026, 9, 30, tzinfo=UTC)


def _task(*, title: str) -> TaskDTO:
    return TaskDTO(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title=title,
        due_at=None,
        status="pending",
        is_overdue=False,
        origin="command",
        original_input=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _candidate(
    *,
    title: str,
    record_type: RecordType = RecordType.TASK,
    all_terms: bool = False,
    word_rank: float | None = None,
    distance: float | None = None,
) -> SearchCandidate:
    task = _task(title=title)
    return SearchCandidate(
        record_type=record_type,
        record_id=task.id,
        item=task,
        all_terms=all_terms,
        word_rank=word_rank,
        distance=distance,
    )


def test_an_all_terms_word_hit_outranks_a_closer_meaning_only_hit() -> None:
    """C-1, FR-6."""
    word_hit = _candidate(
        title="Renew passport", all_terms=True, word_rank=0.01, distance=0.9
    )
    meaning_hit = _candidate(title="Visa papers", distance=0.01)

    ranked = sorted([meaning_hit, word_hit], key=rank_key)

    assert ranked == [word_hit, meaning_hit]


def test_tiers_order_all_terms_then_some_terms_then_meaning() -> None:
    some = _candidate(title="Renew insurance", word_rank=0.9)
    every = _candidate(title="Renew passport", all_terms=True, word_rank=0.1)
    meaning = _candidate(title="Visa", distance=0.1)
    no_vector = _candidate(title="Old note")

    assert sorted([no_vector, meaning, some, every], key=rank_key) == [
        every,
        some,
        meaning,
        no_vector,
    ]


def test_within_the_meaning_tier_the_closer_record_comes_first() -> None:
    near = _candidate(title="Backend role", distance=0.1)
    far = _candidate(title="Spring Boot", distance=0.3)

    assert sorted([far, near], key=rank_key) == [near, far]


def test_groups_cap_at_five_count_every_match_and_follow_the_best_hit() -> None:
    """C-2, FR-7 and FR-8."""
    tasks = [
        _candidate(title=f"Task {index}", distance=0.1 + index / 100)
        for index in range(7)
    ]
    memory = _candidate(
        title="My passport expires in 2030",
        record_type=RecordType.MEMORY,
        all_terms=True,
        word_rank=0.5,
    )

    groups = group_hits(
        candidates=[*tasks, memory],
        totals={RecordType.TASK: 12, RecordType.MEMORY: 1},
        limit=5,
    )

    assert [group.record_type for group in groups] == [
        RecordType.MEMORY,
        RecordType.TASK,
    ]
    task_group = groups[1]
    assert len(task_group.hits) == 5
    assert task_group.total == 12
    assert [hit.item for hit in task_group.hits] == [
        candidate.item for candidate in tasks[:5]
    ]
    assert all(hit.citation is None for group in groups for hit in group.hits)


def test_no_candidates_gives_no_groups() -> None:
    """FR-10: the capture card shows the no-match state."""
    assert group_hits(candidates=[], totals={}, limit=5) == []


def test_a_cited_record_below_the_cut_is_pinned_in() -> None:
    """C-2.5, FR-17: every citation has a row to point at; the total stays."""
    tasks = [
        _candidate(title=f"Task {index}", distance=0.1 + index / 100)
        for index in range(7)
    ]
    cited = tasks[6]

    groups = group_hits(
        candidates=tasks,
        totals={RecordType.TASK: 7},
        limit=5,
        citations={cited.record_id: 1},
    )

    shown = [hit.item for hit in groups[0].hits]
    assert len(shown) == 5
    assert cited.item in shown
    assert tasks[4].item not in shown
    assert groups[0].total == 7
    assert [hit.citation for hit in groups[0].hits if hit.item == cited.item] == [1]
