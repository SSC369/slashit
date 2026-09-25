"""Limits and the extraction contracts for capture. No magic values elsewhere.

Timezone-aware date resolution is a follow-up: slice 2's ``user_settings``
does not exist yet, so every relative date resolves against server UTC. The
adapter appends the reference moment; neither schema mentions it.

**Schema descriptions are kept terse on purpose.** A verbose description on
the ``due_at`` field was measured adding enough generation latency to push a
call from ~5.4s to ~10.7s, past the 8 second budget (NFR-2), with no gain in
accuracy. The detailed guidance lives in the instruction text instead, which
does not carry the same cost. See the dev log, slice 1.
"""

from typing import Any, Final

# Build plan AD-4. Every drawn example in 02-design.md is well under this, and
# it protects the gateway's TPM headroom cheaply.
MAX_INPUT_LENGTH: Final = 500

# The two commands this epic ships. FR-24 (narrowed 2026-09-13): completing,
# editing and deleting a task are records-view actions only, never commands.
KNOWN_COMMANDS: Final[tuple[str, ...]] = (
    "/add-task",
    "/tasks",
    "/remind",
    "/reminders",
)

TASK_EXTRACTION_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "due_at": {"type": "string", "description": "ISO date if one is implied"},
    },
    "required": ["title"],
}

TASK_EXTRACTION_INSTRUCTION: Final = (
    "Extract the task title and, if implied, when it is due, as an absolute "
    "ISO 8601 datetime. Omit due_at if no date or time is implied."
)

# Used only to resolve the answer to a pending due-date question (FR-37,
# FR-38), where the answer is a date phrase with no task title in it, so the
# task schema's required "title" would not fit.
DUE_AT_ONLY_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {"due_at": {"type": "string"}},
    "required": ["due_at"],
}

DUE_AT_ONLY_INSTRUCTION: Final = (
    'The input answers "when is this due". Resolve it to an absolute ISO 8601 datetime.'
)

# FR-45. One page of capture_turns at a time, newest first.
CAPTURE_HISTORY_PAGE_SIZE: Final = 20

# Epic 003. # Build plan §5: the model returns plain fields and never a timestamp. The
# server computes every fire time. Kept terse: capture/constants.py documents
# how schema description length costs generation latency.
REMINDER_EXTRACTION_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "local_date": {"type": "string", "description": "YYYY-MM-DD"},
        "local_time": {"type": "string", "description": "HH:MM, 24-hour"},
        "repeat_kind": {
            "type": "string",
            "enum": ["none", "daily", "weekly", "monthly", "yearly"],
        },
        "repeat_interval": {"type": "integer"},
        "repeat_weekdays": {"type": "array", "items": {"type": "integer"}},
        "day_of_month": {"type": "integer"},
    },
    "required": ["description"],
}

REMINDER_EXTRACTION_INSTRUCTION: Final = (
    "Extract a reminder. description: what to be reminded of, without the time "
    "words. local_date and local_time: when, in the user's own local time, only "
    "if said. repeat_kind: none unless a repeat is said. repeat_interval: N for "
    "'every N'. repeat_weekdays: 0=Monday to 6=Sunday; weekdays means 0 to 4. "
    "day_of_month: for a monthly repeat on a numbered day."
)
