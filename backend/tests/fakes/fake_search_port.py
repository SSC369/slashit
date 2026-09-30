"""An in-memory search for capture's SearchPort (epic 005).

Returns the groups it was given for any text, and records each search, so a
test can assert what capture searched for and that it searched at all.
"""

from dataclasses import dataclass, field
from uuid import UUID

from app.domains.search.interfaces.dtos import SearchGroupDTO
from app.domains.search.public import SearchResultsDTO


@dataclass
class FakeSearchPort:
    groups: list[SearchGroupDTO] = field(default_factory=list)
    meaning_unavailable: bool = False
    searches: list[tuple[UUID, str]] = field(default_factory=list)

    async def search(self, *, user_id: UUID, text: str) -> SearchResultsDTO:
        self.searches.append((user_id, text))
        return SearchResultsDTO(
            query=text,
            groups=list(self.groups),
            meaning_unavailable=self.meaning_unavailable,
        )
