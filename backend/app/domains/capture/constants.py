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
    # Epic 004. `/memory` is deliberately absent (PRD, out of scope): it falls
    # to FR-12's closest-match suggestion, which offers `/memories`.
    "/remember",
    "/add-memory",
    "/memories",
    # `/forget` is deliberately absent since sub-plan 4.5: forget is from a
    # memory's detail page only, and `/forget` falls to FR-12's reply.
    # Epic 005, FR-1.
    "/search",
    # Epic 007, FR-1 and FR-24.
    "/add-event",
    "/events",
)

# Epic 005. Like a memory save (AD-7 below), a search is measured on its text,
# not the whole line, and an over-long one gets a drawn state (FR-3).
SEARCH_COMMAND: Final = "/search"

# Epic 005, FR-2: the one question an empty `/search` asks.
SEARCH_QUESTION: Final = "What should Slashit search for?"

# Epic 004, FR-1: two names for one action.
MEMORY_SAVE_COMMANDS: Final[tuple[str, ...]] = ("/remember", "/add-memory")

# Epic 004, AD-7. A fact's 500-character limit (FR-4) is checked by memories on
# the fact itself, and answered with a drawn state, so a memory command's whole
# line may run past MAX_INPUT_LENGTH. This outer guard still protects the
# gateway from an unbounded line.
MAX_MEMORY_LINE_LENGTH: Final = 1000

# FR-3. The one question an empty `/remember` asks.
FACT_QUESTION: Final = "What should Slashit remember?"

# Epic 004, FR-10. Fixed, so a conflict turn never stores an existing memory's
# text: the old memories are shown live, by id (index §4).
CONFLICT_QUESTION: Final = "Which is correct?"

# What a resolution turn records as the answer. Fixed labels, never typed text.
CONFLICT_ANSWER_LABELS: Final = {
    "keep_new": "Keep the new one",
    "keep_old": "Keep the old one",
    "both": "Both are correct",
}

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

# Epic 007. Build plan §5 and AD-6: the model reads what was said; every rule
# that is arithmetic (next year, overnight, Feb 29, cap) is code. `has_year`
# tells a stated past year (FR-5) from an omitted one (FR-4). Kept terse.
ADD_EVENT_COMMAND: Final = "/add-event"
EVENTS_COMMAND: Final = "/events"

EVENT_EXTRACTION_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
        "has_year": {"type": "boolean"},
        "start_time": {"type": "string", "description": "HH:MM, 24-hour"},
        "end_date": {"type": "string", "description": "YYYY-MM-DD"},
        "end_time": {"type": "string", "description": "HH:MM, 24-hour"},
        "location": {"type": "string"},
        "description": {"type": "string"},
        "repeat_yearly": {"type": "boolean"},
        "alert_leads_minutes": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["title"],
}

EVENT_EXTRACTION_INSTRUCTION: Final = (
    "Extract an event. title: what it is, without date, time, place or alert "
    "words. start_date, start_time, end_date, end_time: local, only if said; a "
    "date with no year is this year. has_year: true only if a year was said. "
    "location: only if a place was said. repeat_yearly: true for every year, "
    "birthdays and anniversaries. alert_leads_minutes: for each 'remind me N "
    "before', N in minutes."
)

# FR-16's one question.
EVENT_ALERT_QUESTION: Final = "Which alert should I keep?"
# The answer to FR-16's question that keeps no alert.
NO_ALERT_ANSWER: Final = "none"
