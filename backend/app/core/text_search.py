"""SQL expressions for epic 005's search, shared by every record repository.

Plumbing only: this builds the word and meaning expressions a repository puts
in its own query. It decides nothing. Which terms, which distance and which
rows are searched are the caller's; how results rank is the search domain's
(build plan AD-3). Each record domain still owns its own query (AD-1).

Terms must be letters and digits only, as every caller's term builder
guarantees, which is what makes joining them into ``to_tsquery`` syntax safe.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import ColumnElement, Float, false, func, literal, or_
from sqlalchemy.orm import InstrumentedAttribute


@dataclass(frozen=True)
class SearchExpressions:
    """The pieces of one search over one table.

    ``matches`` is None when there is nothing to search by: no terms and no
    vector. A caller then returns no rows rather than every row.
    """

    matches: ColumnElement[bool] | None
    all_terms: ColumnElement[bool]
    word_rank: ColumnElement[float]
    distance: ColumnElement[float]
    # Only the parts that vary: PostgreSQL refuses a constant in ORDER BY.
    ordering: tuple[ColumnElement[Any], ...]


def build_search_expressions(
    *,
    search_vector: InstrumentedAttribute[str | None],
    embedding: InstrumentedAttribute[list[float] | None],
    terms: Sequence[str],
    query_embedding: Sequence[float] | None,
    max_distance: float,
) -> SearchExpressions:
    """Word match on any term, all terms, text rank, and cosine distance.

    With no terms the word parts are constant false and NULL. With no query
    vector the distance is NULL and plays no part in ``matches``.
    """
    conditions: list[ColumnElement[bool]] = []
    ordering: list[ColumnElement[Any]] = []
    all_terms: ColumnElement[bool] = false()
    word_rank: ColumnElement[float] = literal(None, type_=Float)
    distance: ColumnElement[float] = literal(None, type_=Float)

    if terms:
        any_query = func.to_tsquery("english", " | ".join(terms))
        all_query = func.to_tsquery("english", " & ".join(terms))
        word_match = search_vector.op("@@")(any_query)
        conditions.append(word_match)
        all_terms = search_vector.op("@@")(all_query)
        # NULL, not zero, when no term is present, so a meaning-only row reads
        # as having no word rank at all (AD-3's tiers).
        word_rank = func.nullif(func.ts_rank(search_vector, any_query), 0)
        ordering += [all_terms.desc(), word_rank.desc().nulls_last()]

    if query_embedding is not None:
        distance = embedding.cosine_distance(list(query_embedding))
        conditions.append(distance < max_distance)
        ordering.append(distance.asc().nulls_last())

    return SearchExpressions(
        matches=or_(*conditions) if conditions else None,
        all_terms=all_terms,
        word_rank=word_rank,
        distance=distance,
        ordering=tuple(ordering),
    )
