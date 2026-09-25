"""The live feed behind the subscription (AD-4, NFR-5).

One ``LISTEN`` connection per process on ``slashit_notifications``. Each
payload names a user and a notification id; it is handed to that user's open
subscriptions and to no one else's. The connection reconnects with backoff;
anything missed while it was down is recovered by the client, which refetches
the list and count when its WebSocket reconnects.

A module-level instance, ``live_signal``, is started and stopped by the API's
lifespan. A process that never starts it (the worker, tests) simply has no
subscribers to feed.
"""

import asyncio
import contextlib
import json
from collections import defaultdict
from uuid import UUID

import asyncpg
import structlog

from app.domains.notifications.constants import (
    LISTEN_HEALTH_CHECK_SECONDS,
    LISTEN_RETRY_FIRST_SECONDS,
    LISTEN_RETRY_MAX_SECONDS,
    NOTIFY_CHANNEL,
)

logger = structlog.get_logger(__name__)


class LiveSubscription:
    """One open subscription's queue of notification ids."""

    def __init__(self, *, signal: "LiveSignal", user_id: UUID) -> None:
        self.signal = signal
        self.user_id = user_id
        self.queue: asyncio.Queue[UUID] = asyncio.Queue()

    async def __aenter__(self) -> "LiveSubscription":
        self.signal.register(subscription=self)
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        self.signal.unregister(subscription=self)

    async def next_notification_id(self) -> UUID:
        return await self.queue.get()


class LiveSignal:
    def __init__(self, *, channel: str) -> None:
        self.channel = channel
        self.subscriptions: dict[UUID, set[LiveSubscription]] = defaultdict(set)
        self.listen_task: asyncio.Task[None] | None = None

    def subscribe(self, *, user_id: UUID) -> LiveSubscription:
        return LiveSubscription(signal=self, user_id=user_id)

    def register(self, *, subscription: LiveSubscription) -> None:
        self.subscriptions[subscription.user_id].add(subscription)

    def unregister(self, *, subscription: LiveSubscription) -> None:
        user_subscriptions = self.subscriptions.get(subscription.user_id)
        if user_subscriptions is None:
            return
        user_subscriptions.discard(subscription)
        if not user_subscriptions:
            del self.subscriptions[subscription.user_id]

    def dispatch_payload(self, *, payload: str) -> None:
        """Route one NOTIFY payload to its user's subscriptions only (NFR-6)."""
        try:
            message = json.loads(payload)
            user_id = UUID(message["user_id"])
            notification_id = UUID(message["notification_id"])
        except (ValueError, KeyError, TypeError):
            logger.warning("notifications.live_signal.bad_payload")
            return
        for subscription in self.subscriptions.get(user_id, set()):
            subscription.queue.put_nowait(notification_id)

    async def start(self, *, dsn: str) -> None:
        if self.listen_task is None:
            self.listen_task = asyncio.create_task(self._listen_forever(dsn=dsn))

    async def stop(self) -> None:
        if self.listen_task is None:
            return
        self.listen_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self.listen_task
        self.listen_task = None

    async def _listen_forever(self, *, dsn: str) -> None:
        retry_seconds = LISTEN_RETRY_FIRST_SECONDS
        while True:
            try:
                await self._listen_until_closed(dsn=dsn)
                retry_seconds = LISTEN_RETRY_FIRST_SECONDS
            except asyncio.CancelledError:
                raise
            # Broad on purpose: whatever broke the connection, the answer is
            # to log it and reconnect, never to let the feed die for good.
            except Exception:
                logger.exception(
                    "notifications.live_signal.lost", retry_seconds=retry_seconds
                )
            await asyncio.sleep(retry_seconds)
            retry_seconds = min(retry_seconds * 2, LISTEN_RETRY_MAX_SECONDS)

    async def _listen_until_closed(self, *, dsn: str) -> None:
        connection = await asyncpg.connect(dsn)
        try:
            await connection.add_listener(self.channel, self._on_notify)
            logger.info("notifications.live_signal.listening")
            while not connection.is_closed():
                await asyncio.sleep(LISTEN_HEALTH_CHECK_SECONDS)
                await connection.execute("SELECT 1")
        finally:
            if not connection.is_closed():
                await connection.close()

    def _on_notify(
        self,
        connection: object,
        pid: int,
        channel: str,
        payload: object,
    ) -> None:
        self.dispatch_payload(payload=str(payload))


live_signal = LiveSignal(channel=NOTIFY_CHANNEL)
