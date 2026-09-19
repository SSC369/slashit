"""Analytics' one use case: record one instrumentation event."""

import uuid

from app.domains.analytics.interactors.record_event import RecordEventInteractor
from app.domains.analytics.interfaces.dtos import RecordEventInputDTO
from tests.fakes.fake_event_repository import FakeEventRepository


async def test_record_event_writes_one_row_with_the_given_type() -> None:
    user_id = uuid.uuid4()
    repository = FakeEventRepository()
    interactor = RecordEventInteractor(event_repository=repository)

    await interactor.record_event(
        dto=RecordEventInputDTO(user_id=user_id, event_type="records_view_opened")
    )

    assert repository.rows == [(user_id, "records_view_opened")]


async def test_each_call_writes_its_own_row() -> None:
    user_id = uuid.uuid4()
    repository = FakeEventRepository()
    interactor = RecordEventInteractor(event_repository=repository)

    await interactor.record_event(
        dto=RecordEventInputDTO(user_id=user_id, event_type="no_command_input")
    )
    await interactor.record_event(
        dto=RecordEventInputDTO(user_id=user_id, event_type="no_command_input")
    )

    assert repository.rows == [
        (user_id, "no_command_input"),
        (user_id, "no_command_input"),
    ]
