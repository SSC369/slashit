"""Memories' queries: the tab and one memory's detail."""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import build_get_memory_interactor, build_list_memories_interactor
from app.domains.memories.graphql.errors import MemoryNotFound
from app.domains.memories.graphql.inputs import MemoriesFilterInput
from app.domains.memories.interactors.dtos import (
    GetMemoryInputDTO,
    ListMemoriesInputDTO,
)
from app.domains.memories.interfaces.dtos import Memory, memory_dto_to_type
from app.domains.memories.interfaces.repositories import CategoryFilter
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

MemoryResult = Annotated[Memory | MemoryNotFound, strawberry.union("MemoryResult")]


def _category_filter(*, memories_filter: MemoriesFilterInput) -> CategoryFilter:
    if memories_filter.uncategorised:
        return "uncategorised"
    return memories_filter.category


@strawberry.type
class MemoryQueries:
    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def memories(
        self,
        info: Info,
        filter_: Annotated[
            MemoriesFilterInput | None, strawberry.argument(name="filter")
        ] = None,
    ) -> list[Memory]:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        memories_filter = filter_ or MemoriesFilterInput()
        interactor = build_list_memories_interactor(context)
        memories = await interactor.list_memories(
            dto=ListMemoriesInputDTO(
                user_id=user_id,
                category=_category_filter(memories_filter=memories_filter),
                search=memories_filter.search,
            )
        )
        return [memory_dto_to_type(memory=memory) for memory in memories]

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def memory(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> MemoryResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_get_memory_interactor(context)
        memory = await interactor.get_memory(
            dto=GetMemoryInputDTO(user_id=user_id, memory_id=UUID(str(id_)))
        )
        return cast(MemoryResult, memory_dto_to_type(memory=memory))
