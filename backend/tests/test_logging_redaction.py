"""Secret redaction cases. See 04.1-api-skeleton.md section 7, case T-1.6.

FR-3 says no application log records the credential, at any level. These cases
are the proof, and the exception case is the one that matters most: a credential
usually reaches a log through a provider error rendered into a traceback, not
through a deliberate log call.
"""

import pytest
import structlog

from app.core.logging import (
    REDACTED,
    blank_user_text,
    build_redactor,
    configure_logging,
)

SECRET = "AIzaSy-not-a-real-key-000000"
SECRETS = frozenset({SECRET})


def _redact(event: dict[str, object]) -> dict[str, object]:
    return dict(build_redactor(SECRETS)(None, "info", event))


def test_secret_in_a_message_is_removed() -> None:
    result = _redact({"event": f"calling provider with {SECRET}"})

    assert SECRET not in str(result)
    assert REDACTED in str(result["event"])


def test_secret_in_a_nested_dict_is_removed() -> None:
    result = _redact({"event": "call", "request": {"headers": {"key": SECRET}}})

    assert SECRET not in str(result)


def test_secret_in_a_list_is_removed() -> None:
    result = _redact({"event": "call", "args": [SECRET, "safe"]})

    assert SECRET not in str(result)
    assert "safe" in str(result)


def test_secret_in_an_exception_is_removed() -> None:
    """The case that catches a credential inside a provider traceback."""
    result = _redact({"event": "failed", "error": ValueError(f"bad key {SECRET}")})

    assert SECRET not in str(result)


def test_no_secrets_configured_leaves_the_event_untouched() -> None:
    """Slice 1 has no secrets, so the processor must be a no-op, not a crash."""
    event = {"event": "hello", "count": 3}

    assert build_redactor(frozenset())(None, "info", dict(event)) == event


def test_memory_text_is_blanked_by_key_at_any_depth() -> None:
    """C-13 of epic 004's sub-plan 4.1, AD-9: a user's text cannot be found by
    value, so every key that may carry it is blanked by name."""
    fact = "My passport number is P1234567"
    event = {
        "event": "memories.saved",
        "text": fact,
        "memory_id": "5b0c",
        "request": {"input_text": f"/remember {fact}", "prompt": fact},
        "turns": [{"original_input": fact}, {"fact": fact}],
        "candidate_text": fact,
    }

    result = blank_user_text(None, "info", event)

    assert fact not in str(result)
    assert result["memory_id"] == "5b0c"
    assert result["event"] == "memories.saved"


def test_the_key_blanking_runs_in_the_configured_pipeline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The processor is not only defined but installed."""
    configure_logging(log_level="INFO", secrets=frozenset(), json_output=True)
    structlog.get_logger("test").info("memories.saved", text="Locker PIN 4417")

    assert "Locker PIN 4417" not in capsys.readouterr().out
