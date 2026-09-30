"""Input DTOs for search's use cases."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

OpenedEventKind = Literal["search_result_opened", "answer_citation_opened"]


@dataclass(frozen=True)
class RecordSearchEventInputDTO:
    """PRD section 8: which result or citation was opened, by position."""

    user_id: UUID
    kind: OpenedEventKind
    position: int
