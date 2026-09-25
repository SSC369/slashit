from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import (
    build_sign_in_interactor,
    build_update_reminder_settings_interactor,
    build_update_timezone_interactor,
)
from app.domains.identity.graphql.errors import (
    AccountLocked,
    AccountNotVerified,
    AuthProviderUnavailable,
    InvalidCredentials,
    InvalidReminderSettings,
    InvalidTimezone,
)
from app.domains.identity.graphql.inputs import (
    SignInInput,
    UpdateReminderSettingsInput,
    UpdateTimezoneInput,
)
from app.domains.identity.graphql.types import (
    ReminderSettingsSaved,
    Settings,
    SignedIn,
    reminder_settings_saved_to_type,
    session_dto_to_type,
    settings_dto_to_type,
)
from app.domains.identity.interactors.dtos import (
    SignInInputDTO,
    UpdateReminderSettingsInputDTO,
    UpdateTimezoneInputDTO,
)
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

UpdateTimezoneResult = Annotated[
    Settings | InvalidTimezone, strawberry.union("UpdateTimezoneResult")
]

UpdateReminderSettingsResult = Annotated[
    ReminderSettingsSaved | InvalidReminderSettings,
    strawberry.union("UpdateReminderSettingsResult"),
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

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def update_reminder_settings(
        self,
        info: Info,
        input_: Annotated[
            UpdateReminderSettingsInput, strawberry.argument(name="input")
        ],
    ) -> UpdateReminderSettingsResult:
        context = cast(Context, info.context)
        interactor = build_update_reminder_settings_interactor(context)
        saved = await interactor.update_reminder_settings(
            dto=UpdateReminderSettingsInputDTO(
                user_id=cast(UUID, context.user_id),
                default_reminder_time=input_.default_reminder_time,
                popups_enabled=input_.popups_enabled,
                email_enabled=input_.email_enabled,
            )
        )
        return cast(
            UpdateReminderSettingsResult, reminder_settings_saved_to_type(saved=saved)
        )

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
