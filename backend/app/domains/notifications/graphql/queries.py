"""Notifications' queries: the panel's page and the bell's count."""

from typing import cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import (
    build_count_unread_interactor,
    build_list_notifications_interactor,
)
from app.domains.notifications.graphql.types import (
    NotificationPage,
    notification_page_to_type,
)
from app.domains.notifications.interactors.dtos import ListNotificationsInputDTO
from app.graphql.permissions import IsAuthenticated


@strawberry.type
class NotificationQueries:
    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def notifications(
        self, info: Info, cursor: str | None = None
    ) -> NotificationPage:
        context = cast(Context, info.context)
        interactor = build_list_notifications_interactor(context)
        page = await interactor.list_notifications(
            dto=ListNotificationsInputDTO(
                user_id=cast(UUID, context.user_id), cursor=cursor
            )
        )
        return notification_page_to_type(page=page)

    @strawberry.field(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def unread_notification_count(self, info: Info) -> int:
        context = cast(Context, info.context)
        interactor = build_count_unread_interactor(context)
        return await interactor.count_unread(user_id=cast(UUID, context.user_id))
