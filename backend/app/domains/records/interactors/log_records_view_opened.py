from uuid import UUID

import structlog

from app.domains.records.interfaces.ports import AnalyticsPort

logger = structlog.get_logger(__name__)


class LogRecordsViewOpenedInteractor:
    def __init__(self, *, analytics: AnalyticsPort) -> None:
        self.analytics = analytics

    async def log_records_view_opened(self, *, user_id: UUID) -> None:
        """Record that the caller opened a records view. PRD section 8's
        metric. Non-blocking: an instrumentation write failure never turns
        this into a user-visible error, same pattern as capture's
        _record_turn."""
        try:
            await self.analytics.record_records_view_opened(user_id=user_id)
        except Exception:
            logger.exception(
                "analytics.records_view_opened_failed", user_id=str(user_id)
            )
