"""Reminder email: TC-3.1 to TC-3.5, FR-14 to FR-18, FR-39."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.domains.notifications.interactors.send_email import SendEmailInteractor
from app.domains.notifications.interfaces.dtos import (
    EmailDeliveryDTO,
    MarkerValue,
    PublishNotification,
)
from app.domains.notifications.interfaces.ports import EmailSendError
from app.domains.notifications.services.email_content import compose_reminder_email
from app.domains.notifications.services.notification_service import (
    NotificationService,
)
from tests.fakes.fake_email import (
    FakeDeliverySettings,
    FakeEmailQueue,
    FakeEmailSender,
    FakeRecipient,
)
from tests.fakes.fake_notification_repository import FakeNotificationRepository

# Wednesday 23 September 2026, 19:00 in Kolkata.
DUE = datetime(2026, 9, 23, 13, 30, tzinfo=UTC)
TARGET = uuid.UUID("7d2b3a6e-0000-4000-8000-000000000001")


def _delivery(*, marker: MarkerValue = "on_time", detail: str = "") -> EmailDeliveryDTO:
    return EmailDeliveryDTO(
        delivery_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        status="queued",
        attempts=0,
        title="Call Mom",
        detail=detail,
        marker=marker,
        occurred_at=DUE,
        time_zone="Asia/Kolkata",
        target_id=TARGET,
        notification_created_at=DUE,
    )


def test_the_on_time_email() -> None:
    """TC-3.1, FR-15."""
    content = compose_reminder_email(
        delivery=_delivery(), app_base_url="https://app.test/", now=DUE
    )

    assert content.subject == "Reminder: Call Mom"
    assert "Today, 7:00 PM · Asia/Kolkata" in content.text
    assert f"https://app.test/records/reminders/{TARGET}" in content.text
    assert "Done or snooze it in Slashit. You need to be signed in." in content.text
    assert "You get this because email reminders are on." in content.text
    assert f'href="https://app.test/records/reminders/{TARGET}"' in content.html


def test_the_late_email() -> None:
    """TC-3.1, FR-17."""
    content = compose_reminder_email(
        delivery=_delivery(marker="late", detail="Every week on Wed"),
        app_base_url="https://app.test",
        now=DUE + timedelta(hours=3),
    )

    assert content.subject == "Late reminder: Call Mom"
    assert "Due Wed 23 Sep, 7:00 PM · every week on Wed" in content.text
    assert (
        "Sent late. This was due Wed 23 Sep at 7:00 PM, and Slashit could not "
        "send it on time." in content.text
    )


def test_a_title_is_escaped_in_html() -> None:
    delivery = _delivery()
    delivery = EmailDeliveryDTO(**{**delivery.__dict__, "title": "<b>Call</b>"})
    content = compose_reminder_email(
        delivery=delivery, app_base_url="https://a", now=DUE
    )
    assert "<b>Call</b>" not in content.html
    assert "&lt;b&gt;Call&lt;/b&gt;" in content.html


class World:
    def __init__(
        self, *, email_enabled: bool = True, is_email_configured: bool = True
    ) -> None:
        self.repository = FakeNotificationRepository()
        self.queue = FakeEmailQueue()
        self.user_id = uuid.uuid4()
        self.service = NotificationService(
            notification_repository=self.repository,
            delivery_settings=FakeDeliverySettings(email_enabled=email_enabled),
            email_queue=self.queue,
            is_email_configured=is_email_configured,
            now_provider=lambda: DUE,
        )

    def publish_for(
        self, *, marker: MarkerValue = "on_time", source_id: uuid.UUID | None = None
    ) -> PublishNotification:
        return PublishNotification(
            user_id=self.user_id,
            kind="reminder",
            source_id=source_id or uuid.uuid4(),
            target_id=TARGET,
            title="Call Mom",
            detail="",
            marker=marker,
            occurred_at=DUE,
            time_zone="Asia/Kolkata",
        )

    def email_statuses(self) -> list[str]:
        return [delivery.status for delivery in self.repository.emails.values()]


async def test_an_on_time_firing_queues_one_email() -> None:
    world = World()
    await world.service.publish(publish=world.publish_for())
    assert world.email_statuses() == ["queued"]
    assert len(world.queue.queued) == 1


@pytest.mark.parametrize(
    ("email_enabled", "is_email_configured", "marker"),
    [(False, True, "on_time"), (True, False, "on_time"), (True, True, "missed")],
)
async def test_off_unconfigured_or_missed_sends_nothing(
    email_enabled: bool, is_email_configured: bool, marker: MarkerValue
) -> None:
    """TC-3.2, FR-14, FR-18, index §9's kill switch."""
    world = World(email_enabled=email_enabled, is_email_configured=is_email_configured)
    notification = await world.service.publish(publish=world.publish_for(marker=marker))
    assert notification is not None
    assert world.email_statuses() == ["skipped"]
    assert world.queue.queued == []


async def test_the_fifty_first_email_is_paused_with_one_notice() -> None:
    """TC-3.3, FR-39."""
    world = World()
    for _ in range(50):
        await world.service.publish(publish=world.publish_for())

    await world.service.publish(publish=world.publish_for())
    await world.service.publish(publish=world.publish_for())

    statuses = world.email_statuses()
    assert statuses.count("queued") == 50
    notices = [
        row for row in world.repository.rows.values() if row.kind == "email_paused"
    ]
    assert len(notices) == 1
    assert notices[0].title == "Email paused until tomorrow"
    reminder_rows = [
        row for row in world.repository.rows.values() if row.kind == "reminder"
    ]
    assert len(reminder_rows) == 52


async def test_a_repeat_publish_requeues_a_waiting_email_and_writes_nothing() -> None:
    """TC-3.4, FR-16, AD-3: the first call stopped between commit and queue."""
    world = World()
    publish = world.publish_for(source_id=uuid.uuid4())
    await world.service.publish(publish=publish)
    world.queue.queued.clear()  # as if the process died before queueing

    repeat = await world.service.publish(publish=publish)

    assert repeat is None
    assert len(world.repository.rows) == 1
    assert len(world.queue.queued) == 1


async def _queued_delivery(world: World) -> uuid.UUID:
    await world.service.publish(publish=world.publish_for())
    return world.queue.queued[0]


def _sender_interactor(
    *, world: World, sender: FakeEmailSender, address: str | None = "a@example.test"
) -> SendEmailInteractor:
    return SendEmailInteractor(
        notification_repository=world.repository,
        recipient=FakeRecipient(address=address),
        sender=sender,
        app_base_url="https://app.test",
        now_provider=lambda: DUE + timedelta(seconds=40),
    )


async def test_send_once_with_the_delivery_id_as_idempotency_key() -> None:
    """TC-3.5, AD-3."""
    world = World()
    delivery_id = await _queued_delivery(world)
    sender = FakeEmailSender()
    interactor = _sender_interactor(world=world, sender=sender)

    first = await interactor.send_email(delivery_id=delivery_id)
    second = await interactor.send_email(delivery_id=delivery_id)

    assert (first, second) == ("sent", "skipped")
    assert [sent["idempotency_key"] for sent in sender.sent] == [str(delivery_id)]
    assert world.email_statuses() == ["sent"]


async def test_a_refused_send_retries_then_fails_on_the_fifth() -> None:
    """TC-3.5: raise to retry; the fifth failure marks it failed."""
    world = World()
    delivery_id = await _queued_delivery(world)
    interactor = _sender_interactor(world=world, sender=FakeEmailSender(failures=5))

    for _ in range(4):
        with pytest.raises(EmailSendError):
            await interactor.send_email(delivery_id=delivery_id)
    final = await interactor.send_email(delivery_id=delivery_id)

    assert final == "failed"
    assert world.email_statuses() == ["failed"]
    assert world.repository.emails[delivery_id].attempts == 5


async def test_no_address_fails_without_sending() -> None:
    world = World()
    delivery_id = await _queued_delivery(world)
    sender = FakeEmailSender()

    outcome = await _sender_interactor(
        world=world, sender=sender, address=None
    ).send_email(delivery_id=delivery_id)

    assert outcome == "failed"
    assert sender.sent == []
