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
    # Epic 006, FR-1 and FR-23.
    "/add-expense",
    "/expenses",
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
# gateway from an unbounded line. Epic 006 gives `/add-expense` the same guard,
# so FR-13's long-description refusal answers a long line (dev log E-3).
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

# A clock time as typed: "4pm", "6:30 am", "18:00", "midnight", "noon". Only a
# midnight the text names is kept (dev log D-15).
EVENT_NAMED_TIME_PATTERN: Final = (
    r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b|\b\d{1,2}:\d{2}\b|\bmidnight\b|\bnoon\b"
)

# FR-16's one question.
EVENT_ALERT_QUESTION: Final = "Which alert should I keep?"
# The answer to FR-16's question that keeps no alert.
NO_ALERT_ANSWER: Final = "none"

# Epic 006, FR-1.
ADD_EXPENSE_COMMAND: Final = "/add-expense"

# Epic 006, FR-23. Read by code, no model call (build plan AD-5).
EXPENSES_COMMAND: Final = "/expenses"

# Index §4. The model lists every number that could be the price; code keeps
# only those typed (AD-4). Kept terse, for the latency reason at the top of
# this file. ``date_words`` is the user's own phrase for the date, for FR-8's
# question. Optional fields are omitted rather than typed nullable, the shape
# every other capture schema uses with this provider. Both changes from index
# §4 are dev log D-1.
EXPENSE_EXTRACTION_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "amounts": {"type": "array", "items": {"type": "string"}},
        "currency": {"type": "string"},
        "description": {"type": "string"},
        "category": {
            "type": "string",
            "enum": [
                "food",
                "transport",
                "shopping",
                "bills",
                "health",
                "entertainment",
                "travel",
                "other",
            ],
        },
        "local_date": {"type": "string"},
        "date_words": {"type": "string"},
    },
    "required": ["amounts", "description", "category"],
}

# The category guide is the user's own split, from the NFR-4 evaluation set
# (tests/eval/expense_categories.json). Amounts include counts, per FR-5's
# own example: "2 coffees 180" asks which number is the price (dev log D-4).
EXPENSE_CATEGORY_GUIDE: Final = (
    "Categories: food is meals, snacks, drinks and groceries. transport is "
    "getting around within a city: cabs, autos, metro, fuel, parking. travel "
    "is a trip away: trains, buses or flights between cities, hotels, and "
    "cabs taken on the trip. bills is rent, utilities, phone, internet, "
    "insurance and subscriptions such as Netflix. health is medicine, doctors, "
    "tests and gyms. entertainment is movies, events, games and books. "
    "shopping is clothes, gadgets and things for the home. other is services "
    "and fees: haircuts, laundry, courier, bank and ATM charges, stamp paper, "
    "and anything unsure."
)

EXPENSE_EXTRACTION_INSTRUCTION: Final = (
    "Read one spend in Indian rupees. amounts: every number written in the "
    "text that could be the price, as typed, counts included; skip only dates "
    "and times. currency: an ISO code only if the text names one, else omit. "
    "description: what was bought, in the user's own words, without the amount "
    "or the date; empty if the text does not say. local_date: the spend's date "
    "as YYYY-MM-DD, omitted for today; a day with no month is the most recent "
    "such day not after today. date_words: the words that gave the date, if "
    f"any. {EXPENSE_CATEGORY_GUIDE}"
)

# Build plan Q5: a description given later costs one more call, to read its
# category. A failure saves as Other (FR-10).
EXPENSE_CATEGORY_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "category": EXPENSE_EXTRACTION_SCHEMA["properties"]["category"],
    },
    "required": ["category"],
}

EXPENSE_CATEGORY_INSTRUCTION: Final = (
    f"The input says what a spend was for. Pick its category. {EXPENSE_CATEGORY_GUIDE}"
)

# Design §8, FR-3 to FR-5 and FR-8.
EXPENSE_AMOUNT_QUESTION: Final = "How much was it?"
EXPENSE_AMOUNT_RETRY: Final = "Enter an amount such as 850 or 1,200.50"
EXPENSE_DESCRIPTION_QUESTION: Final = "What was the expense for?"
# FR-2 as amended 2026-10-03 (dev log E-2): the line's refusal, and the
# question asked again when an answer is past the ceiling.
EXPENSE_AMOUNT_TOO_LARGE: Final = (
    "That amount is too large to save. Check it for an extra zero."
)
EXPENSE_AMOUNT_CHOICE_QUESTION: Final = "Which number is the amount?"
# Dev log E-5, user decision 2026-10-03: a chip answers FR-5's question as this
# prefix and the candidate's paise, so typed digits are always rupees. Mirrored
# by the frontend's EXPENSE_CHIP_ANSWER_PREFIX.
EXPENSE_CHIP_ANSWER_PREFIX: Final = "chip:"
EXPENSE_DATE_QUESTION: Final = (
    "{phrase} reads as {date}, which is after today. Save it for that date?"
)
# When the model gave no phrase for the date it read.
EXPENSE_DATE_PHRASE_FALLBACK: Final = "Your date"
