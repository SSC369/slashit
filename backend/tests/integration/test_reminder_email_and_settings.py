"""Slice 3 against a real database: a fired reminder is emailed once to the
account's own address (TC-3.8), and reminder settings stay with their owner
(TC-3.9). The sender and the queue are fakes: no email leaves the test."""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql import text

from app.core import auth as auth_module
from app.core.db import user_transaction
from app.core.settings import Settings
from app.domains.identity.repositories.auth_account_repository import (
    SqlAuthAccountRepository,
)
from app.domains.identity.repositories.settings_repository import SqlSettingsRepository
from app.domains.identity.services.identity_service import IdentityService
from app.domains.notifications.adapters.identity_settings_adapter import (
    IdentityDeliverySettingsAdapter,
    IdentityRecipientAdapter,
)
from app.domains.notifications.interactors.send_email import SendEmailInteractor
from app.domains.notifications.repositories.notification_repository import (
    SqlNotificationRepository,
)
from app.domains.notifications.services.notification_service import (
    NotificationService,
)
from app.domains.reminders.adapters.notifications_adapter import NotificationsAdapter
from app.domains.reminders.interactors.fire_one import FireOneInteractor
from app.domains.reminders.repositories.reminder_repository import SqlReminderRepository
from tests.fakes.fake_email import FakeEmailQueue, FakeEmailSender


def _now() -> datetime:
    return datetime.now(UTC)


async def _seed_due(
    session_factory: async_sessionmaker[AsyncSession], *, user_id: uuid.UUID
) -> tuple[uuid.UUID, datetime]:
    reminder_id = uuid.uuid4()
    fire_at = datetime.now(UTC).replace(microsecond=0) - timedelta(seconds=30)
    async with session_factory() as session, user_transaction(session, user_id) as s:
        await s.execute(
            text(
                "INSERT INTO reminders (id, user_id, description, repeat_kind, "
                "repeat_interval, repeat_weekdays, local_time, anchor_local_date, "
                "one_time_at, next_fire_at, schedule_timezone, state, origin, "
                "created_at, updated_at) VALUES (:id, :user_id, 'Call Mom', 'none', "
                "1, '{}', :local_time, :anchor, :fire_at, :fire_at, 'Asia/Kolkata', "
                "'upcoming', 'command', now(), now())"
            ),
            {
                "id": reminder_id,
                "user_id": user_id,
                "local_time": time(19),
                "anchor": date.today(),
                "fire_at": fire_at,
            },
        )
    return reminder_id, fire_at


def _fire_one(*, session: AsyncSession, queue: FakeEmailQueue) -> FireOneInteractor:
    """As deps wires it, with email configured and a fake queue."""
    service = NotificationService(
        notification_repository=SqlNotificationRepository(session),
        delivery_settings=IdentityDeliverySettingsAdapter(
            identity_service=IdentityService(
                settings_repository=SqlSettingsRepository(session)
            )
        ),
        email_queue=queue,
        is_email_configured=True,
        now_provider=_now,
    )
    return FireOneInteractor(
        reminder_repository=SqlReminderRepository(session),
        notifications=NotificationsAdapter(notification_service=service),
        now_provider=_now,
    )


async def test_a_fired_reminder_is_emailed_once_to_the_account(
    session_factory: async_sessionmaker[AsyncSession],
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-3.8, FR-14, FR-16."""
    user_a, _ = two_users
    reminder_id, fire_at = await _seed_due(session_factory, user_id=user_a)
    queue = FakeEmailQueue()
    async with session_factory() as session:
        await _fire_one(session=session, queue=queue).fire_one(
            reminder_id=reminder_id, scheduled_for=fire_at
        )
        await _fire_one(session=session, queue=queue).fire_one(
            reminder_id=reminder_id, scheduled_for=fire_at
        )
    [delivery_id] = queue.queued
    sender = FakeEmailSender()

    async with session_factory() as session:
        interactor = SendEmailInteractor(
            notification_repository=SqlNotificationRepository(session),
            recipient=IdentityRecipientAdapter(
                identity_service=IdentityService(
                    settings_repository=SqlSettingsRepository(session),
                    auth_account_repository=SqlAuthAccountRepository(session),
                )
            ),
            sender=sender,
            app_base_url="https://app.test",
            now_provider=_now,
        )
        first = await interactor.send_email(delivery_id=delivery_id)
        second = await interactor.send_email(delivery_id=delivery_id)

    async with session_factory() as session:
        status = await session.scalar(
            text("SELECT status::text FROM notification_deliveries WHERE id = :id"),
            {"id": delivery_id},
        )
    assert (first, second) == ("sent", "skipped")
    assert [sent["to"] for sent in sender.sent] == [f"{user_a}@rls-test.invalid"]
    assert sender.sent[0]["subject"] == "Reminder: Call Mom"
    assert status == "sent"


@pytest.fixture
def signing_key(monkeypatch: pytest.MonkeyPatch) -> ec.EllipticCurvePrivateKey:
    key = ec.generate_private_key(ec.SECP256R1())
    public_key = key.public_key()

    class FakeKey:
        key = public_key

    class FakeClient:
        def get_signing_key_from_jwt(self, _token: str) -> FakeKey:
            return FakeKey()

    monkeypatch.setattr(auth_module, "_get_jwks_client", lambda _s: FakeClient())
    return key


def _headers(
    key: ec.EllipticCurvePrivateKey, settings: Settings, *, user_id: uuid.UUID
) -> dict[str, str]:
    claims: dict[str, Any] = {
        "sub": str(user_id),
        "iss": settings.jwt_issuer,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    return {"Authorization": f"Bearer {jwt.encode(claims, key, algorithm='ES256')}"}


async def _graphql(
    client: AsyncClient, *, query: str, headers: dict[str, str], **variables: Any
) -> dict[str, Any]:
    response = await client.post(
        "/graphql", json={"query": query, "variables": variables}, headers=headers
    )
    body: dict[str, Any] = response.json()
    assert "errors" not in body, body
    result: dict[str, Any] = body["data"]
    return result


SAVE = """
mutation($input: UpdateReminderSettingsInput!) {
  updateReminderSettings(input: $input) {
    __typename
    ... on ReminderSettingsSaved {
      showBothOffWarning
      settings { defaultReminderTime popupsEnabled emailEnabled }
    }
    ... on InvalidReminderSettings { field }
  }
}
"""
READ = "query { settings { defaultReminderTime popupsEnabled emailEnabled } }"


async def test_reminder_settings_save_and_stay_with_their_owner(
    client: AsyncClient,
    signing_key: ec.EllipticCurvePrivateKey,
    settings: Settings,
    two_users: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """TC-3.9, FR-31, FR-32, FR-34, NFR-6."""
    user_a, user_b = two_users
    a_headers = _headers(signing_key, settings, user_id=user_a)
    b_headers = _headers(signing_key, settings, user_id=user_b)

    off = await _graphql(
        client,
        query=SAVE,
        headers=a_headers,
        input={
            "defaultReminderTime": "07:30",
            "popupsEnabled": False,
            "emailEnabled": False,
        },
    )
    invalid = await _graphql(
        client, query=SAVE, headers=a_headers, input={"defaultReminderTime": "nine"}
    )
    a_read = await _graphql(client, query=READ, headers=a_headers)
    b_read = await _graphql(client, query=READ, headers=b_headers)

    assert off["updateReminderSettings"] == {
        "__typename": "ReminderSettingsSaved",
        "showBothOffWarning": True,
        "settings": {
            "defaultReminderTime": "07:30",
            "popupsEnabled": False,
            "emailEnabled": False,
        },
    }
    assert invalid["updateReminderSettings"] == {
        "__typename": "InvalidReminderSettings",
        "field": "defaultReminderTime",
    }
    assert a_read["settings"]["defaultReminderTime"] == "07:30"
    assert b_read["settings"] == {
        "defaultReminderTime": "09:00",
        "popupsEnabled": True,
        "emailEnabled": True,
    }
