"""Notifications' mutations: mark one read, mark all read (FR-37)."""

from typing import Annotated, cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import (
    build_mark_all_read_interactor,
    build_mark_notification_read_interactor,
)
from app.domains.notifications.graphql.errors import NotificationNotFound
from app.domains.notifications.graphql.types import MarkAllNotificationsReadSucceeded
from app.domains.notifications.interactors.dtos import MarkNotificationReadInputDTO
from app.domains.notifications.interfaces.dtos import (
    Notification,
    notification_dto_to_type,
)
from app.graphql.error_mapping import map_errors
from app.graphql.permissions import IsAuthenticated

MarkNotificationReadResult = Annotated[
    Notification | NotificationNotFound, strawberry.union("MarkNotificationReadResult")
]


@strawberry.type
class NotificationMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    @map_errors
    async def mark_notification_read(
        self,
        info: Info,
        id_: Annotated[strawberry.ID, strawberry.argument(name="id")],
    ) -> MarkNotificationReadResult:
        context = cast(Context, info.context)
        interactor = build_mark_notification_read_interactor(context)
        notification = await interactor.mark_notification_read(
            dto=MarkNotificationReadInputDTO(
                user_id=cast(UUID, context.user_id), notification_id=UUID(str(id_))
            )
        )
        return cast(
            MarkNotificationReadResult,
            notification_dto_to_type(notification=notification),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def mark_all_notifications_read(
        self, info: Info
    ) -> MarkAllNotificationsReadSucceeded:
        context = cast(Context, info.context)
        interactor = build_mark_all_read_interactor(context)
        marked_count = await interactor.mark_all_read(
            user_id=cast(UUID, context.user_id)
        )
        return MarkAllNotificationsReadSucceeded(marked_count=marked_count)
