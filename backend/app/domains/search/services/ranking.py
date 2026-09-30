"""AD-3: how search orders what the record domains matched. Pure.

Three tiers: every term present, then some term present, then meaning alone.
Word tiers order by text rank, the meaning tier by distance. A record with
every searched word therefore always outranks one matched by meaning alone,
however close (FR-6).
"""

from app.domains.search.interfaces.dtos import (
    RecordType,
    SearchCandidate,
    SearchGroupDTO,
    SearchHitDTO,
)

# Sorts a record with no vector after every record that has one.
_NO_DISTANCE = 9.0


def rank_key(candidate: SearchCandidate) -> tuple[int, float, float]:
    """Smaller sorts first."""
    if candidate.all_terms:
        tier = 2
    elif candidate.word_rank is not None:
        tier = 1
    else:
        tier = 0
    distance = candidate.distance if candidate.distance is not None else _NO_DISTANCE
    return (-tier, -(candidate.word_rank or 0.0), distance)


def group_hits(
    *,
    candidates: list[SearchCandidate],
    totals: dict[RecordType, int],
    limit: int,
) -> list[SearchGroupDTO]:
    """FR-7 and FR-8: one group per record type with matches, at most
    ``limit`` hits each, best first; groups ordered by their best hit."""
    by_type: dict[RecordType, list[SearchCandidate]] = {}
    for candidate in sorted(candidates, key=rank_key):
        by_type.setdefault(candidate.record_type, []).append(candidate)
    groups = [
        SearchGroupDTO(
            record_type=record_type,
            hits=[
                SearchHitDTO(
                    record_type=record_type, item=candidate.item, citation=None
                )
                for candidate in ranked[:limit]
            ],
            total=max(totals.get(record_type, 0), len(ranked)),
        )
        for record_type, ranked in by_type.items()
    ]
    # dict preserves insertion order, and insertion followed the global rank,
    # so each group already sits where its best hit ranks.
    return groups
