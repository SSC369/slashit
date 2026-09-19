from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import build_sign_in_interactor, build_update_timezone_interactor
from app.domains.identity.graphql.errors import (
    AccountLocked,
    AccountNotVerified,
    AuthProviderUnavailable,
    InvalidCredentials,
    InvalidTimezone,
)
from app.domains.identity.graphql.inputs import SignInInput, UpdateTimezoneInput
from app.domains.identity.graphql.types import (
    Settings,
    SignedIn,
    session_dto_to_type,
    settings_dto_to_type,
)
from app.domains.identity.interactors.dtos import SignInInputDTO, UpdateTimezoneInputDTO
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

UpdateTimezoneResult = Annotated[
    Settings | InvalidTimezone, strawberry.union("UpdateTimezoneResult")
]

SignInResult = Annotated[
    SignedIn
    | InvalidCredentials
    | AccountLocked
    | AccountNotVerified
    | AuthProviderUnavailable,
    strawberry.union("SignInResult"),
]


@strawberry.type
class IdentityMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def update_timezone(
        self,
        info: Info,
        input_: Annotated[UpdateTimezoneInput, strawberry.argument(name="input")],
    ) -> UpdateTimezoneResult:
        context = cast(Context, info.context)
        user_id = cast(UUID, context.user_id)
        interactor = build_update_timezone_interactor(context)
        settings = await interactor.update_timezone(
            dto=UpdateTimezoneInputDTO(user_id=user_id, timezone=input_.timezone)
        )
        return cast(UpdateTimezoneResult, settings_dto_to_type(settings=settings))

    @strawberry.mutation
    @map_errors
    async def sign_in(
        self,
        info: Info,
        input_: Annotated[SignInInput, strawberry.argument(name="input")],
    ) -> SignInResult:
        """No permission class: this is how a caller gets a session in the
        first place, so it cannot require one. FR-17's lockout, not
        IsAuthenticated, is what closes this off to abuse."""
        context = cast(Context, info.context)
        interactor = build_sign_in_interactor(context)
        session = await interactor.sign_in(
            dto=SignInInputDTO(email=input_.email, password=input_.password)
        )
        return cast(SignInResult, session_dto_to_type(session=session))
