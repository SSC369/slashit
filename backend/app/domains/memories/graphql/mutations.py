"""Memories' mutations: edit (FR-18) and forget from Records (FR-21)."""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import build_forget_memory_interactor, build_update_memory_interactor
from app.domains.memories.graphql.errors import InvalidMemory, MemoryNotFound
from app.domains.memories.graphql.inputs import UpdateMemoryInput
from app.domains.memories.interactors.dtos import (
    ForgetMemoryInputDTO,
    UpdateMemoryInputDTO,
)
from app.domains.memories.interfaces.dtos import (
    MemoriesForgotten,
    Memory,
    MemoryTooLong,
    memory_dto_to_type,
)
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

UpdateMemoryResult = Annotated[
    Memory | MemoryTooLong | InvalidMemory | MemoryNotFound,
    strawberry.union("UpdateMemoryResult"),
]
ForgetMemoryResult = Annotated[
    MemoriesForgotten | MemoryNotFound, strawberry.union("ForgetMemoryResult")
]


@strawberry.type
class MemoryMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def update_memory(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
        input_: Annotated[UpdateMemoryInput, strawberry.argument(name="input")],
    ) -> UpdateMemoryResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_update_memory_interactor(context)
        memory = await interactor.update_memory(
            dto=UpdateMemoryInputDTO(
                user_id=user_id,
                memory_id=UUID(str(id_)),
                text=input_.text,
                category=input_.category,
            )
        )
        return cast(UpdateMemoryResult, memory_dto_to_type(memory=memory))

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def forget_memory(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> ForgetMemoryResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_forget_memory_interactor(context)
        forgotten = await interactor.forget_memory(
            dto=ForgetMemoryInputDTO(user_id=user_id, memory_id=UUID(str(id_)))
        )
        return cast(ForgetMemoryResult, MemoriesForgotten(count=forgotten.count))
