"""The reminder email, on time or late (FR-15, FR-17, `ReminderEmail`). Pure:
the notification and a clock in, subject, HTML and plain text out.

Hard-coded colours are the design's accepted debt (§6): mail clients ignore
CSS variables.
"""

from datetime import datetime, timedelta
from html import escape
from zoneinfo import ZoneInfo

from app.domains.notifications.interfaces.dtos import EmailContent, EmailDeliveryDTO

_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_OPEN_LINE = "Done or snooze it in Slashit. You need to be signed in."
_FOOTER_LINE = "You get this because email reminders are on."


def _clock(*, local: datetime) -> str:
    hour_12 = local.hour % 12 or 12
    return f"{hour_12}:{local.minute:02d} {'AM' if local.hour < 12 else 'PM'}"


def _day(*, local: datetime) -> str:
    return f"{_WEEKDAYS[local.weekday()]} {local.day} {local:%b}"


def _describe_set_time(*, instant: datetime, zone: ZoneInfo, now: datetime) -> str:
    """ "Today, 7:00 PM", "Tomorrow, 9:00 AM", or "Sun 21 Sep, 6:00 PM"."""
    local = instant.astimezone(zone)
    today = now.astimezone(zone).date()
    if local.date() == today:
        return f"Today, {_clock(local=local)}"
    if local.date() == today - timedelta(days=1):
        return f"Yesterday, {_clock(local=local)}"
    return f"{_day(local=local)}, {_clock(local=local)}"


def compose_reminder_email(
    *, delivery: EmailDeliveryDTO, app_base_url: str, now: datetime
) -> EmailContent:
    zone = ZoneInfo(delivery.time_zone)
    local_due = delivery.occurred_at.astimezone(zone)
    is_late = delivery.marker == "late"
    when = _describe_set_time(instant=delivery.occurred_at, zone=zone, now=now)
    repeat = (
        delivery.detail[:1].lower() + delivery.detail[1:] if delivery.detail else ""
    )

    subject = f"{'Late reminder' if is_late else 'Reminder'}: {delivery.title}"
    if is_late:
        meta = f"Due {_day(local=local_due)}, {_clock(local=local_due)}"
        meta = f"{meta} · {repeat}" if repeat else meta
        late_note = (
            f"Sent late. This was due {_day(local=local_due)} at "
            f"{_clock(local=local_due)}, and Slashit could not send it on time."
        )
    else:
        meta = f"{when} · {delivery.time_zone}"
        late_note = ""

    base = app_base_url.rstrip("/")
    open_url = f"{base}/records/reminders/{delivery.target_id}"
    settings_url = f"{base}/settings"

    text_lines = [
        "Reminder",
        delivery.title,
        meta,
        *([late_note] if late_note else []),
        "",
        f"Open in Slashit: {open_url}",
        _OPEN_LINE,
        "",
        f"{_FOOTER_LINE} Change email settings: {settings_url}",
    ]
    return EmailContent(
        subject=subject,
        html=_render_html(
            title=delivery.title,
            meta=meta,
            late_note=late_note,
            open_url=open_url,
            settings_url=settings_url,
        ),
        text="\n".join(text_lines),
    )


def _render_html(
    *, title: str, meta: str, late_note: str, open_url: str, settings_url: str
) -> str:
    late_block = (
        f'<p style="margin:16px 0 0;padding:12px 14px;border-radius:8px;'
        f'background:#f8f1e6;color:#2f2823;font-size:14px">{escape(late_note)}</p>'
        if late_note
        else ""
    )
    return (
        '<div style="background:#faf8f4;padding:32px 16px;'
        "font-family:'IBM Plex Sans',Helvetica,Arial,sans-serif;color:#2f2823\">"
        '<div style="max-width:480px;margin:0 auto;background:#ffffff;'
        'border:1px solid #e7e0d5;border-radius:12px;padding:28px">'
        '<div style="font-family:monospace;font-size:18px;margin-bottom:20px">'
        'slash<span style="color:#8a5a2b">.</span>it</div>'
        '<div style="font-size:11px;font-weight:600;letter-spacing:.07em;'
        'text-transform:uppercase;color:#9c9389">Reminder</div>'
        '<div style="font-size:22px;font-weight:600;margin-top:6px">'
        f"{escape(title)}</div>"
        f'<div style="font-size:14px;color:#6b625a;margin-top:6px">{escape(meta)}</div>'
        f"{late_block}"
        f'<a href="{escape(open_url)}" style="display:inline-block;margin-top:22px;'
        "padding:11px 18px;border-radius:8px;background:#2f5ea8;color:#ffffff;"
        'font-weight:600;text-decoration:none">Open in Slashit</a>'
        f'<p style="font-size:13px;color:#6b625a;margin:12px 0 0">{_OPEN_LINE}</p>'
        "</div>"
        '<p style="max-width:480px;margin:16px auto 0;font-size:12px;color:#9c9389">'
        f'{_FOOTER_LINE} <a href="{escape(settings_url)}" style="color:#2f5ea8">'
        "Change email settings</a></p></div>"
    )
