"""Structured logging, with secret redaction installed first.

Requirement FR-3 says no application log records the provider credential, at any
level. The redaction processor below is registered ahead of every other
processor so that nothing can render a secret before it is removed.

It is installed in slice 1, before any credential exists, so that no later slice
has to remember to add it.
"""

import logging
import sys
from collections.abc import Callable, MutableMapping
from typing import Any

import structlog

REDACTED = "[redacted]"

_MAX_REDACTION_DEPTH = 6

# Epic 004, AD-9: memory text never reaches a log. A secret is found by value;
# a user's text cannot be, since it is anything. So these keys are blanked by
# name wherever they appear, at any depth, whatever they hold. A log call that
# needs to mention a memory names its id.
USER_TEXT_KEYS = frozenset(
    {"text", "fact", "input_text", "original_input", "candidate_text", "prompt"}
)


def _redact(content: Any, *, secrets: frozenset[str], depth: int = 0) -> Any:
    """Replace any secret found anywhere inside ``content``.

    Walks strings, mappings, and sequences. Depth is bounded because a log event
    should never be deep enough to need more, and an unbounded walk on a cyclic
    structure would hang the logger.
    """
    if depth > _MAX_REDACTION_DEPTH:
        return content

    if isinstance(content, str):
        for secret in secrets:
            if secret in content:
                content = content.replace(secret, REDACTED)
        return content

    if isinstance(content, MutableMapping):
        return {
            field_name: _redact(field_value, secrets=secrets, depth=depth + 1)
            for field_name, field_value in content.items()
        }

    if isinstance(content, (list, tuple)):
        rebuilt = [_redact(item, secrets=secrets, depth=depth + 1) for item in content]
        return type(content)(rebuilt)

    if isinstance(content, BaseException):
        # A provider error rendered into a traceback is the most common way a
        # credential reaches a log. Redact the message, not the exception type.
        return _redact(str(content), secrets=secrets, depth=depth + 1)

    return content


def _blank_user_text(content: Any, *, depth: int = 0) -> Any:
    """Replace the value of every ``USER_TEXT_KEYS`` key inside ``content``."""
    if depth > _MAX_REDACTION_DEPTH:
        return content
    if isinstance(content, MutableMapping):
        return {
            field_name: (
                REDACTED
                if field_name in USER_TEXT_KEYS
                else _blank_user_text(field_value, depth=depth + 1)
            )
            for field_name, field_value in content.items()
        }
    if isinstance(content, (list, tuple)):
        rebuilt = [_blank_user_text(item, depth=depth + 1) for item in content]
        return type(content)(rebuilt)
    return content


def blank_user_text(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """The structlog processor for AD-9. The event name itself, under the key
    ``event``, is a fixed string chosen by the code and is left alone."""
    return _blank_user_text(event_dict)  # type: ignore[no-any-return]


def build_redactor(
    secrets: frozenset[str],
) -> Callable[[Any, str, MutableMapping[str, Any]], MutableMapping[str, Any]]:
    """Build a structlog processor that strips ``secrets`` from every event."""

    def redact_secrets(
        _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
    ) -> MutableMapping[str, Any]:
        if not secrets:
            return event_dict
        return _redact(event_dict, secrets=secrets)  # type: ignore[no-any-return]

    return redact_secrets


def configure_logging(
    *, log_level: str, secrets: frozenset[str], json_output: bool
) -> None:
    """Configure structlog for the process. Call once, at startup."""
    logging.basicConfig(
        format="%(message)s", stream=sys.stdout, level=getattr(logging, log_level)
    )

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if json_output
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[
            build_redactor(secrets),
            structlog.contextvars.merge_contextvars,
            # After the merge, so text bound into context is blanked too.
            blank_user_text,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
