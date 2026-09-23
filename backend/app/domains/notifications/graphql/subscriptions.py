"""The live feed (FR-13, AD-4). One subscription, filtered to its own user."""

from collections.abc import AsyncGenerator
from typing import cast
from uuid import UUID

import strawberry
from strawberry.types import Info

from app.core.context import Context
from app.core.deps import build_stream_notifications_interactor
from app.domains.notifications.interfaces.dtos import (
    Notification,
    notification_dto_to_type,
)
from app.graphql.permissions import IsAuthenticated


@strawberry.type
class NotificationSubscriptions:
    @strawberry.subscription(permission_classes=[IsAuthenticated])  # type: ignore[untyped-decorator]
    async def notification_received(
        self, info: Info
    ) -> AsyncGenerator[Notification, None]:
        context = cast(Context, info.context)
        interactor = build_stream_notifications_interactor(context)
        async for notification in interactor.stream_notifications(
            user_id=cast(UUID, context.user_id)
        ):
            yield notification_dto_to_type(notification=notification)
