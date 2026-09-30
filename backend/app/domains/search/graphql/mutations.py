"""Search's mutations: one, for PRD section 8's open events."""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import build_record_search_event_interactor
from app.domains.search.graphql.inputs import RecordSearchEventInput, SearchEventKind
from app.domains.search.interactors.dtos import (
    OpenedEventKind,
    RecordSearchEventInputDTO,
)
from app.graphql.permissions import IsAuthenticated

_KIND: dict[SearchEventKind, OpenedEventKind] = {
    SearchEventKind.SEARCH_RESULT_OPENED: "search_result_opened",
    SearchEventKind.ANSWER_CITATION_OPENED: "answer_citation_opened",
}


@strawberry.type
class SearchMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def record_search_event(
        self,
        info: Info,
        input_: Annotated[RecordSearchEventInput, strawberry.argument(name="input")],
    ) -> bool:
        """The frontend calls this when a result or a citation is opened."""
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_record_search_event_interactor(context)
        await interactor.record_search_event(
            dto=RecordSearchEventInputDTO(
                user_id=user_id, kind=_KIND[input_.kind], position=input_.position
            )
        )
        return True
