"""Changing the stored timezone, and refusing an invalid one. FR-28, error table.
003 TC-4.4: a real change is announced so reminders can move (AD-6)."""

import uuid

import pytest

from app.domains.identity.graphql.errors import InvalidTimezoneError
from app.domains.identity.interactors.dtos import UpdateTimezoneInputDTO
from app.domains.identity.interactors.update_timezone import UpdateTimezoneInteractor
from tests.fakes.fake_settings_repository import FakeSettingsRepository
from tests.fakes.fake_timezone_change_queue import FakeTimezoneChangeQueue


def _interactor(
    *, repository: FakeSettingsRepository, queue: FakeTimezoneChangeQueue
) -> UpdateTimezoneInteractor:
    return UpdateTimezoneInteractor(
        settings_repository=repository, timezone_change_queue=queue
    )


async def test_changes_the_stored_timezone() -> None:
    user_id = uuid.uuid4()
    repository = FakeSettingsRepository()
    queue = FakeTimezoneChangeQueue()
    await repository.upsert(user_id=user_id, timezone="Asia/Kolkata")

    settings = await _interactor(repository=repository, queue=queue).update_timezone(
        dto=UpdateTimezoneInputDTO(user_id=user_id, timezone="Europe/London")
    )

    assert settings.timezone == "Europe/London"
    assert queue.announced_user_ids == [user_id]


async def test_saving_the_same_zone_announces_nothing() -> None:
    """TC-4.4."""
    user_id = uuid.uuid4()
    repository = FakeSettingsRepository()
    queue = FakeTimezoneChangeQueue()
    await repository.upsert(user_id=user_id, timezone="Asia/Kolkata")

    await _interactor(repository=repository, queue=queue).update_timezone(
        dto=UpdateTimezoneInputDTO(user_id=user_id, timezone="Asia/Kolkata")
    )

    assert queue.announced_user_ids == []


async def test_invalid_timezone_is_refused_and_nothing_is_stored() -> None:
    """T-2.12 of 002; TC-4.4 of 003: nothing is announced either."""
    user_id = uuid.uuid4()
    repository = FakeSettingsRepository()
    queue = FakeTimezoneChangeQueue()

    with pytest.raises(InvalidTimezoneError):
        await _interactor(repository=repository, queue=queue).update_timezone(
            dto=UpdateTimezoneInputDTO(user_id=user_id, timezone="not/a/zone")
        )

    assert await repository.get_for_user(user_id=user_id) is None
    assert queue.announced_user_ids == []
