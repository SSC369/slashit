"""Reminder settings: TC-3.6, TC-3.7, and FR-31, FR-32 defaults."""

import uuid
from datetime import UTC, datetime, time

import pytest

from app.domains.identity.graphql.errors import InvalidReminderSettingsError
from app.domains.identity.interactors.dtos import UpdateReminderSettingsInputDTO
from app.domains.identity.interactors.update_reminder_settings import (
    UpdateReminderSettingsInteractor,
)
from tests.fakes.fake_settings_repository import FakeSettingsRepository

NOW = datetime(2026, 9, 23, 10, 0, tzinfo=UTC)


def _interactor(
    *, repository: FakeSettingsRepository
) -> UpdateReminderSettingsInteractor:
    return UpdateReminderSettingsInteractor(
        settings_repository=repository, now_provider=lambda: NOW
    )


async def test_a_change_keeps_every_other_setting() -> None:
    """FR-31, FR-32: defaults for a user with no row, then one change at a time."""
    repository = FakeSettingsRepository()
    user_id = uuid.uuid4()
    interactor = _interactor(repository=repository)

    saved = await interactor.update_reminder_settings(
        dto=UpdateReminderSettingsInputDTO(
            user_id=user_id,
            default_reminder_time="07:30",
            popups_enabled=None,
            email_enabled=None,
        )
    )

    assert saved.settings.default_reminder_time == time(7, 30)
    assert (saved.settings.popups_enabled, saved.settings.email_enabled) == (True, True)
    assert saved.show_both_off_warning is False


async def test_turning_both_off_warns_once() -> None:
    """TC-3.6, FR-34."""
    repository = FakeSettingsRepository()
    user_id = uuid.uuid4()
    interactor = _interactor(repository=repository)

    first = await interactor.update_reminder_settings(
        dto=UpdateReminderSettingsInputDTO(
            user_id=user_id,
            default_reminder_time=None,
            popups_enabled=False,
            email_enabled=False,
        )
    )
    await interactor.update_reminder_settings(
        dto=UpdateReminderSettingsInputDTO(
            user_id=user_id,
            default_reminder_time=None,
            popups_enabled=True,
            email_enabled=None,
        )
    )
    again = await interactor.update_reminder_settings(
        dto=UpdateReminderSettingsInputDTO(
            user_id=user_id,
            default_reminder_time=None,
            popups_enabled=False,
            email_enabled=None,
        )
    )

    assert first.show_both_off_warning is True
    assert first.settings.channels_off_warned_at == NOW
    assert again.show_both_off_warning is False


async def test_a_default_time_that_is_not_a_time_is_refused() -> None:
    """TC-3.7."""
    repository = FakeSettingsRepository()
    user_id = uuid.uuid4()

    with pytest.raises(InvalidReminderSettingsError) as refused:
        await _interactor(repository=repository).update_reminder_settings(
            dto=UpdateReminderSettingsInputDTO(
                user_id=user_id,
                default_reminder_time="nine",
                popups_enabled=None,
                email_enabled=None,
            )
        )

    assert refused.value.field == "defaultReminderTime"
    assert repository.rows == {}
