"""Sends email through Resend's HTTP API. The only place Resend is named (AD-8).

``httpx`` rather than Resend's SDK: it is already installed, and the call is
one POST (index §2).
"""

import httpx

from app.domains.notifications.constants import (
    RESEND_EMAILS_URL,
    RESEND_TIMEOUT_SECONDS,
)
from app.domains.notifications.interfaces.ports import EmailSendError


class ResendEmailSender:
    def __init__(self, *, api_key: str, sender: str) -> None:
        self.api_key = api_key
        self.sender = sender

    async def send(
        self, *, idempotency_key: str, to: str, subject: str, html: str, text: str
    ) -> str:
        """Resend drops a second request with the same idempotency key, so a
        retried job never sends twice (AD-3)."""
        try:
            async with httpx.AsyncClient(timeout=RESEND_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    RESEND_EMAILS_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Idempotency-Key": idempotency_key,
                    },
                    json={
                        "from": self.sender,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                        "text": text,
                    },
                )
        except httpx.HTTPError as error:
            raise EmailSendError(
                f"Resend unreachable: {type(error).__name__}"
            ) from error
        if response.status_code >= 400:
            # Status only: the body can echo the address, which is never logged.
            raise EmailSendError(
                f"Resend refused the email: HTTP {response.status_code}"
            )
        message_id = response.json().get("id")
        return str(message_id) if message_id else ""
