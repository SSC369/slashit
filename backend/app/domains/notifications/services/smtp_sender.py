"""Sends email through a local SMTP server, before a sending domain is
verified in Resend (index note, 003 dev log 2026-09-26). The only place
``smtplib`` is used.

Local only: SMTP has no idempotency key, so a retried job can send twice. That
risk is accepted here because this sender only ever runs with
``ENVIRONMENT=local`` (`app/core/deps.py`); `ResendEmailSender` keeps AD-3's
dedupe guarantee everywhere else.
"""

import smtplib
from asyncio import to_thread
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.domains.notifications.interfaces.ports import EmailSendError


class SmtpEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool,
        sender: str,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.sender = sender

    async def send(
        self, *, idempotency_key: str, to: str, subject: str, html: str, text: str
    ) -> str:
        """Returns ``idempotency_key`` back: SMTP has no message id to give."""
        await to_thread(self._send_sync, to=to, subject=subject, html=html, text=text)
        return idempotency_key

    def _send_sync(self, *, to: str, subject: str, html: str, text: str) -> None:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = to
        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as client:
                if self.use_tls:
                    client.starttls()
                if self.username:
                    client.login(self.username, self.password)
                client.send_message(message)
        except (smtplib.SMTPException, OSError) as error:
            raise EmailSendError(f"SMTP send failed: {type(error).__name__}") from error
