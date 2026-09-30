"""Search's queries: the records view's search, and a detail's related list.

`relatedRecords` is its own query so a slow or failed list never holds up the
detail it sits on (FR-28, build plan §4).
"""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import (
    build_list_related_records_interactor,
    build_search_records_interactor,
)
from app.domains.search.constants import PAGE_LIMIT_MAX
from app.domains.search.interactors.dtos import (
    ListRelatedRecordsInputDTO,
    SearchRecordsInputDTO,
)
from app.domains.search.interfaces.dtos import (
    RecordType,
    SearchPage,
    SearchRecord,
    SearchTooLong,
    related_records_to_type,
    search_page_to_type,
)
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

SearchPageResult = Annotated[
    SearchPage | SearchTooLong, strawberry.union("SearchPageResult")
]


@strawberry.type
class SearchQueries:
    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def search(
        self,
        info: Info,
        text: str,
        record_type: RecordType | None = None,
        offset: int = 0,
        limit: int = PAGE_LIMIT_MAX,
    ) -> SearchPageResult:
        context = cast(Context, info.context)
        interactor = build_search_records_interactor(context)
        page = await interactor.search_records(
            dto=SearchRecordsInputDTO(
                user_id=cast(UUID, context.user_id),
                text=text,
                record_type=record_type,
                offset=offset,
                limit=limit,
            )
        )
        return search_page_to_type(page=page)

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def related_records(
        self,
        info: Info,
        record_type: RecordType,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> list[SearchRecord]:
        context = cast(Context, info.context)
        interactor = build_list_related_records_interactor(context)
        related = await interactor.list_related_records(
            dto=ListRelatedRecordsInputDTO(
                user_id=cast(UUID, context.user_id),
                record_type=record_type,
                record_id=UUID(str(id_)),
            )
        )
        return related_records_to_type(related=related)
