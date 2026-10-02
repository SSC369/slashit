---
doc: dev-log
feature: 007-events
title: Events
stage: 5
status: draft
owner: claude
created: 2026-10-02
updated: 2026-10-02
approved_on: null
supersedes: null
---

# Dev Log — Events

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-capture-and-browse.md)

What actually happened. Deviations from the approved plan are recorded the day
they happen, per rule 5 of the root ruleset.

## Base

Branch `feat/007-events` in the worktree `../jarvis-007`, from `main` at
`56da5b6`. Built in parallel with 006, whose migrations share the numbers
`0037` and `0038`; whichever merges second renumbers. Slice 1 merged to `main`
first, on 2026-10-02, so 006 renumbers. Work continues from `main`; the
worktree is retired.

Tests run against a local PostgreSQL database, `slashit_007_test`, with the
model faked. The worktree's `backend/.env` points at the hosted database, so
every run sets `DATABASE_URL` to the local one.

## Slice 1 — Capture and browse

### Tasks

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|
| T-1.1 | 4.1 | Migrations, model, RLS boundary test | done | `0037_calendar_events`, `0038_capture_events`. Down to `0036` and up again on the local database. The RLS boundary test enumerates every table, `calendar_events` included |
| T-1.2 | 4.1 | `schedule.py` with unit and property tests | done | `test_event_schedule.py`: every date rule in §7, and 1,000 random schedules across twelve zones (FR-12, NFR-3) |
| T-1.3 | 4.1 | Repository and `EventService`, with the cap | done | Cap and concurrent-create cases pass, in unit and integration tests |
| T-1.4 | 4.1 | Events GraphQL `event`, `events` | done | `test_events_graphql.py` |
| T-1.5 | 4.1 | Capture: schema, instruction, `/add-event`, `/events` | done | `test_event_capture.py`. D-1 |
| T-1.6 | 4.1 | Capture questions: no date, two leads | done | FR-2 and FR-16 cases pass. D-2 |
| T-1.7 | 4.1 | Records: Events tab and All | done | Events in the `records` union and the All tab |
| T-1.8 | 4.1 | Analytics event and redaction test | done | `event_created` carries five presence flags and no text (T6) |
| T-1.9 | 4.1 | Frontend store, fragments, operations, codegen | done | `EventsStore` with computed orderings; `GetEvents`, `GetEvent`; event members in `SubmitCapture`, `AnswerPendingCapture`, `GetRecords`. D-3 |
| T-1.10 | 4.1 | Frontend capture cards and `/events` card | done | `EventCards.tsx`: saved, saving, alert question, cap refusal, month-grouped list, empty, error. Date question chips in `TurnCard`. D-4, D-5 |
| T-1.11 | 4.1 | Frontend Records tab, All marker, detail, routes | done | `EventTable`, `EventsController`, `EventDetailView`, `EventDetailController`; diamond row under All; `/records/events`, `/records/events/:id`. D-5, D-6, D-7 |
| T-1.12 | 4.1 | Design deltas in tokens, both themes | done | Three primitives, three semantics, dark values in both dark blocks. D-8 |
| T-1.13 | 4.1 | Labelled set and live extraction and latency run | owed | Needs a provider key in the build environment. NFR-1 and NFR-2 unmeasured |
| T-1.14 | 4.1 | Browser pass against the canvas | owed | Needs a signed-in session against the hosted project |

### Tests at the end of the slice

Frontend: 327 pass, type-check and production build clean, lint unchanged (one
pre-existing warning in `main.tsx`).

Backend: everything passes except eight, none caused by this slice:

| Test | Why it fails here |
|---|---|
| 5 in `test_firing_and_notifications.py` | `AppNotOpen` from the job queue. Fails the same way on untouched `56da5b6` in this environment |
| `test_rls_boundary.py::test_identity_does_not_survive_the_transaction` | Asserts the connection role is `postgres`; the local database's owner role is the developer's own |
| `test_memory_eval_live.py`, `test_search_eval_live.py` | Live runs; need a provider key |

### Deviations

| # | Date | Planned | Actual | Why | Approved by |
|---|---|---|---|---|---|
| D-1 | 2026-10-02 | §5: `normalise_capture` returns rule codes; capture turns them into copy; "no copy in events" | Events writes the notes as finished sentences, returned as `Event.whenNotes`; the client places a "Read from" note under Repeat and every other under When | One place owns the wording the card and any later caller show | — |
| D-2 | 2026-10-02 | Design §8: "When is the dentist appointment?" | `When is “Dentist appointment”?`, the title quoted as extracted | The title is not rewritten into a sentence; quoting it reads correctly for any title | — |
| D-3 | 2026-10-02 | `EventFields` selects `status` and `description` | Aliased as `eventStatus` and `eventDescription` | GraphQL rejects the `RecordItem` union query otherwise: `Task.status` is `String!` and `Event.status` an enum; `Reminder.description` is `String!` and `Event.description` nullable | — |
| D-4 | 2026-10-02 | `EventAsk` draws a "Pick a date" chip | It opens the browser's own date picker and sends the chosen day as the answer | No date control exists in the design system; the native picker needs none | — |
| D-5 | 2026-10-02 | `Main` and the detail artboards draw Edit, and the detail Delete | Not drawn in slice 1 | Edit and delete are slice 2 (§1 of 4.1). The saved card keeps Open in Records | — |
| D-6 | 2026-10-02 | `RecordsEvents` draws the search box on the Events tab | Hidden on the Events tab, and a search typed on another tab is ignored there | Events are not searchable until slice 2 (FR-30). Showing the box would list other types' matches under Events | — |
| D-7 | 2026-10-02 | `EmptyEvents.tsx`; error states as a red note inside a card | Empty, error and signed-out use the shared notice card the Reminders tab and tasks already use | One notice component for every Records tab | — |
| D-8 | 2026-10-02 | Design §6: `.grouphead` dark value | The shared group heading's ground moved from `--color-background` to the new `--color-group-head`, so the Reminders tab's headings change too | Design §6 gives `.grouphead` its own value in both themes, and the light one, `#fbf8f3`, is 003's drawn value | — |

### Defects and incidents

| Date | What happened | Cause | Fix |
|---|---|---|---|
| 2026-10-02 | The first backend run went to the hosted database named in `backend/.env`, not the local one, and stopped at its first failure | The worktree's `.env` points at the hosted database | Every later run sets `DATABASE_URL` to `slashit_007_test`. The fixtures delete their test users on teardown. Two `@rls-test.invalid` users with no timestamps remain on the hosted database; whether from this run is unknown, so they were left for the user |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-10-02 | Created. Slice 1 recorded: T-1.1 to T-1.12 done, T-1.13 and T-1.14 owed, D-1 to D-8 | Slice 1 built | — |
| 2026-10-02 | Slice 1 committed as `fb0a767` and merged to `main` | User: "commit changes and push to main" | user |
