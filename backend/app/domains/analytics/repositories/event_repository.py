"""The only SQL for events. Returns nothing, an insert-only log."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import user_transaction
from app.domains.analytics.interfaces.dtos import EventType
from app.domains.analytics.models import Event


class SqlEventRepository:
    """Against the request's own session, same pattern as task_repository.py."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(self, *, user_id: uuid.UUID, event_type: EventType) -> None:
        async with user_transaction(self.session, user_id) as scoped:
            scoped.add(
                Event(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    event_type=event_type,
                    occurred_at=datetime.now(UTC),
                )
            )
