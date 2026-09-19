"""Records' side of the "weekly actives opening a records view" metric,
PRD section 8."""

import uuid

from app.domains.records.interactors.log_records_view_opened import (
    LogRecordsViewOpenedInteractor,
)
from tests.fakes.fake_analytics_port import FakeAnalyticsPort


async def test_logs_one_records_view_opened_event() -> None:
    user_id = uuid.uuid4()
    analytics = FakeAnalyticsPort()
    interactor = LogRecordsViewOpenedInteractor(analytics=analytics)

    await interactor.log_records_view_opened(user_id=user_id)

    assert analytics.records_view_opened_calls == [user_id]


async def test_an_analytics_failure_does_not_raise() -> None:
    """Non-blocking, same reasoning as capture's _record_turn: instrumentation
    never turns into a user-visible error."""

    class RaisingAnalyticsPort:
        async def record_records_view_opened(self, *, user_id: uuid.UUID) -> None:
            raise RuntimeError("boom")

    interactor = LogRecordsViewOpenedInteractor(analytics=RaisingAnalyticsPort())

    await interactor.log_records_view_opened(user_id=uuid.uuid4())
