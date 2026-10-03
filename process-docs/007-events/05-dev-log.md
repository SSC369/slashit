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
| T-1.13 | 4.1 | Labelled set and live extraction and latency run | done, NFR-1 misses | 2026-10-02. Set `tests/eval/event_extraction.json`, 60 lines, drafted by Claude, awaiting the user's correction. Scorer `tests/integration/test_event_eval_live.py`. NFR-2 passes, NFR-1 misses; see Live measurements |
| T-1.14 | 4.1 | Browser pass against the canvas | done, dark only, with findings | 2026-10-02, against the hosted project with a second account. See Browser pass |

### Live measurements

Run 2026-10-02 against the real model, on the local database
`slashit_007_test`, clock fixed at Friday 2026-10-02 10:00 Asia/Kolkata.

| NFR | Target | Measured | Result |
|---|---|---|---|
| NFR-2, field extraction | over 90% of fields | 98.1%, 530 of 540 fields over 60 lines | pass |
| NFR-1, acknowledgement | under 1.5 s at p95 | Saving card shown on submit, before the request; covered by `TurnCard.test.tsx` | pass, after the PRD change |
| Server time, recorded not gated | none | 3.29 s p95, 2.67 s median, 3.30 s max over 20 `/add-event` captures | recorded |

NFR-1 was timed from submit to the full GraphQL response, and every capture
waits on one model call, so 1.5 s could not be met. The user chose to measure
it at the client's saving card instead; PRD change log, 2026-10-02.

After D-15, NFR-2 reran at 98.3%: no invented midnights remain.

The ten NFR-2 misses:

| Kind | Lines | Effect |
|---|---|---|
| A time invented for a date-only event: `00:00`, `00:00` to `23:59` | Rahul's wedding, housewarming | Saved at midnight instead of all day. Fixed by D-15 |
| An end time invented from a start time | gym trial `08:00`, health checkup `09:00`, anniversary dinner `20:00` | An end the user never gave; harmless where it equals the start |
| `repeat_yearly` true for a dated chore | health checkup, car insurance renewal | The event repeats every year unasked |
| A location read from a title word | Office Diwali celebration, location `office` | Minor |

### Browser pass

Run 2026-10-02 in Chrome against `localhost:5173` and the hosted project.
The first account hit its daily limit of 20 model calls, so the pass used a
second account.

Matched: `Main`'s saved cards, `EventAsk`'s date question and alert choice,
`EventsList`, `RecordsEvents`, `RecordsAllEvents` and `EventDetail`. The
loading, empty, saving and daily-limit states also matched. The differences
already logged were seen as logged: D-2, D-5, D-6.

| # | Finding | Artboard | Kind |
|---|---|---|---|
| B-1 | The first command typed after the page loads is dropped: no turn, nothing saved. Seen twice, on two accounts | `Main` | defect |
| B-2 | Alert choice chips show the lead only, "1 hour before"; the canvas adds the date, "1 week before · Sat 14 Nov" | `EventAsk` | design gap |
| B-3 | Timezone reads `Asia/Calcutta`, the legacy name the browser reports; the canvas shows `Asia/Kolkata` | `EventDetail` | design gap |
| B-4 | "Dentist Friday 4pm", typed on a Friday evening, saved as today and already past, with no question | `Main` | product question |
| B-5 | "Team dinner 8pm" saved as 8:00 to 9:00 PM, an end never given. The same miss as T-1.13's end times | `Main` | extraction |
| B-6 | Light theme not compared: this Chrome renders every page dark, the light canvas artboards included | all light | owed |

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
| D-9 | 2026-10-02 | Index §5 table: `pending_captures.candidate_event` jsonb | No column. The pending question keeps the typed sentence in `known_title`; the answer re-runs extraction on it, with the date appended or the chosen lead kept | The `/remind` pattern already does this, and no schema change is needed. Costs one extra model call per answer | — |
| D-10 | 2026-10-02 | Index §5 table: analytics types `event_created`, `event_edited`, `event_alert_not_set` in slice 1 | Only `event_created` added in `0038` | Edit and the alert are slice 2; their types land with them | — |
| D-11 | 2026-10-02 | Index §7, 4.1 §6: `event(id)` returns `null` for a missing or foreign id | Returns the union member `EventNotFound` | Matches reminders' `ReminderNotFound`; errors are data (backend repo rules §8) | — |
| D-12 | 2026-10-02 | Index §7: a date range whose end cannot follow its start shows the not-saved card | The end is dropped and the event saves as a single day | The not-saved card is drawn for a model outage only; a dropped end is visible in the confirmation | — |
| D-13 | 2026-10-02 | Not in the design | `/add-event` with no title asks "What is the event?" | Every capture command asks when its subject is missing (001's confirmation model); no artboard draws it | — |
| D-14 | 2026-10-02 | Build plan §4: `events(include: EventScope = UPCOMING)` | `events(scope: EventScope = UPCOMING)` | Naming only | — |
| D-15 | 2026-10-02 | 4.1 §5: the model's fields are read as given | `read_event_fields` drops a `00:00` start, and a `00:00` or `23:59` end with it, unless the text names a time | T-1.13 found the model giving date-only events a midnight start. Unit cases in `test_event_capture.py` | user |
| D-16 | 2026-10-03 | Build plan §10: alert and event "set in one transaction" | Two transactions, ordered: event then alerts on create and edit, alerts then event on delete. The 15-minute roll sweep repairs any mismatch | Each domain writes in its own `user_transaction`; a shared one would give every reminders write a second mode. 4.2 Q1 | user |

### Decisions during the build

| # | Date | Decision | Effect | Approved by |
|---|---|---|---|---|
| X-1 | 2026-10-02 | An event may carry any number of alerts, no cap. Reverses epic Q5, "One alert in V1" | Change record on the epic (Q5) and PRD (FR-1, FR-14, FR-16, the non-goal on line 52). Re-opens design, build plan and the plan index. Slice 1 stores one alert, so a migration follows, and FR-16's "which alert?" question goes. Slice 2's sub-plan is drafted for many alerts | user |

### Pending

| # | Item | Blocks | Owner |
|---|---|---|---|
| ~~P-0~~ | X-1: epic and PRD change records approved 2026-10-03, PRD Q3 and Q4 answered. Design change record and canvas redraw approved 2026-10-03. Build plan change record approved 2026-10-03, AD-8 locked. Index and 4.1 change records approved 2026-10-03. **Done 2026-10-03.** Slice 1's built "which alert?" question (FR-16, now removed) goes in slice 2 | Slice 2 | Claude, then user approval |
| P-1 | Review D-1 to D-14 (D-15 approved) and approve each, or ask for a change | Closing slice 1 | user |
| P-2 | Review the 60-line set `tests/eval/event_extraction.json` | Shipping | user |
| P-3 | Decide B-1 to B-5 from the browser pass; B-6 light-theme pass in a browser without forced dark | Shipping | user, then Claude |
| P-4 | **Next task.** Sub-plan `04.2-alerts-and-manage.md` approved 2026-10-03; build slice 2, T-2.1 to T-2.16: any number of alerts per event, set, fire, re-arm yearly and follow edits; convert `alert_lead_minutes`; remove FR-16's question; edit and delete; search and related; timezone change | Slice 2 code | Claude, then user approval |
| P-5 | The two `@rls-test.invalid` users left on the hosted database, see Defects | Nothing | user: delete or keep |

### Defects and incidents

| Date | What happened | Cause | Fix |
|---|---|---|---|
| 2026-10-02 | The first backend run went to the hosted database named in `backend/.env`, not the local one, and stopped at its first failure | The worktree's `.env` points at the hosted database | Every later run sets `DATABASE_URL` to `slashit_007_test`. The fixtures delete their test users on teardown. Two `@rls-test.invalid` users with no timestamps remain on the hosted database; whether from this run is unknown, so they were left for the user |

## Slice 2 — Alerts and manage

Built on branch `feat/007-events-slice-2`, cut from `docs/007-events-x1-alerts`
(PR #4). Tests run against a fresh local PostgreSQL 16, `slashit_007_test`,
with pgvector and a stub of Supabase's `auth` schema and roles, migrated one
revision at a time. Python 3.12 virtualenv; the model is faked.

### Tasks

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|
| T-2.1 | 4.2 | Migration `0042_event_alerts`, models | done | Up, down and up again on the local database with two events, one with a lead. Up gives `{1440}` and `{}`; a lead of -1 or 525601 is refused by `ck_event_alert_leads`; down keeps the first lead only, as documented. `test_event_alerts_schema.py` guards the result (C-18). See D-17. Storage now reads and writes the list; the API still shows one lead until T-2.4 |
| T-2.2 | 4.2 | `normalise_leads`, `alert_fire_times` | done | Pure, in `schedule.py`. `NormalisedLeads.had_repeat` drives the "named twice, kept once" note; `AlertTime` pairs are sorted soonest first, the order the cap sets them in. Four unit cases (C-1 to C-3 and out-of-range leads). Slice 1's `_read_leads` in `create_event.py` goes in T-2.4 |
| T-2.3 | 4.2 | Reminders: `set_event_alerts`, `clear_event_alerts`, `event_id` filters, alert firing kind | done | `SetEventAlertsInteractor` sorts soonest first, names passed and over-cap alerts, and replaces the event's live rows in one transaction; the cap counts every live row but the event's own. `ClearEventAlertsInteractor` soft-deletes them and hides notifications whose target is the event. Reminders' list, search and embed queries skip `event_id` rows, so the Reminders tab, `/reminders`, search and rezone never see them; `get_by_id` does not, so Done and Snooze still reach an alert. Firing an alert row publishes `event_alert` with `target_id` the event and `action_target_id` the row; notifications treat both firing kinds alike for email, Done, Snooze and once-per-firing. Nine unit cases, five against PostgreSQL (C-5 to C-7, FR-19, FR-21, FR-23, T7). See D-18 |
| T-2.4 | 4.2 | Create arms alerts; capture drops FR-16's question; `alertsNotSet` | done | `EventAlertArming` (events' services) sets one alert per stored lead through `RemindersAlertsAdapter`, then drops from the event any lead not set, so an event lists only alerts that will fire; edit and the roll reuse it. Leads pass through `normalise_leads`, which now reports which leads repeated, for the "named twice, kept once" note. `Event.alerts` and `Event.alertNotes` added; `EventCreated.alertsNotSet` per build plan §4. The single `alertLeadMinutes`, `alertText`, `alertFiresAt` repeat the soonest alert until the client moves to the list in T-2.10. Capture's `EventAlertChoiceAsked`, its question and `/add-event`'s second question are gone; a pending `event_alert_choice` row saves every lead (C-20). Cases C-1, C-2, C-4, C-20, the cap and an outage, unit and against PostgreSQL. See D-19 |
| T-2.5 | 4.2 | `updateEvent`, `deleteEvent` with the write order of Q1 | done | `UpdateEventInteractor` validates the form (empty or long text, end date before start, end time without a start), writes under the same per-user lock as create, refuses an edit that would make a 501st upcoming event as `EventInvalid` reason `LIMIT`, and re-arms through `EventAlertArming` only when the title, schedule or leads changed. The event keeps its origin and typed command. `DeleteEventInteractor` clears the alerts, then soft-deletes. Results `EventUpdated` (with `alertsNotSet`), `EventInvalid`, `EventNotFound`, `EventDeleted`; a non-UUID id reads as not found. Eleven unit cases, four over GraphQL against PostgreSQL, every union member produced (C-8 to C-10, C-15, C-17 for edit and delete) |

### Deviations

| # | Date | Plan said | Built | Why | Approved by |
|---|---|---|---|---|---|
| D-17 | 2026-10-03 | 4.2 tables: `notifications` gains a kind and `action_target_id` | Also a unique index `uq_notifications_event_alert_source` on `source_id` where `action_target_id IS NOT NULL` | One notification per firing for event alerts, as 003 AD-3 gives reminders. The existing unique index covers kind `reminder` only, and a predicate cannot name an enum value added in the same transaction | — |
| D-18 | 2026-10-03 | Index §4: `set_event_alerts(user_id, event_id, title, fire_times, now)` | `set_event_alerts(user_id, event_id, title, alerts, origin, now)`, each alert an `EventAlertRequest(fires_at, detail)`; `reminders.alert_detail text`, added to `0042` before it left this branch | An alert's notification must name the lead and the event's date (FR-18, design `EventAlertToast`), and reminders knows neither. Events writes the line, such as "1 day before · Mon 12 Oct, all day", when it sets the alert. The toast's head shows "Event alert" and the lead leads the detail line, chosen by the user over a lead column on notifications | user |
| D-19 | 2026-10-03 | 4.2 §6: event saved, then setting alerts fails, "Capture shows the event saved with its alerts not set, reason unknown" | The confirmation shows the event with its alerts, and names none as not set; the leads stay stored and the 15-minute sweep sets them | A third "unknown" reason would need copy the design never drew, for a failure the sweep repairs within 15 minutes. Logged with the event id | — |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-10-02 | Created. Slice 1 recorded: T-1.1 to T-1.12 done, T-1.13 and T-1.14 owed, D-1 to D-8 | Slice 1 built | — |
| 2026-10-02 | Slice 1 committed as `fb0a767` and merged to `main` | User: "commit changes and push to main" | user |
| 2026-10-02 | T-1.13 run: 60-line set and live scorer added; NFR-2 98.1% pass, NFR-1 3.29 s p95 miss | User chose to close slice 1's checks | user |
| 2026-10-02 | NFR-1 measured at the saving card; D-15 fixes invented midnights; NFR-2 rerun 98.3% | User chose both recommended options | user |
| 2026-10-02 | T-1.14 browser pass run, dark theme; findings B-1 to B-6 | User chose to close slice 1's checks | user |
| 2026-10-02 | X-1 recorded: any number of alerts per event; P-0 added as the next task | User: "allow any number of alerts" | user |
| 2026-10-02 | D-9 to D-14 logged, found on review; Pending section added | User asked for the pending items in the dev log | user |
| 2026-10-03 | P-0 updated: epic and PRD change records for X-1 drafted, then approved with PRD Q3 and Q4 answered | User chose to start P-0, then approved | user |
| 2026-10-03 | P-0 updated: design change record drafted, canvas republished with 3 new and 11 changed artboards | User chose to write the design change record, then approved | user |
| 2026-10-03 | P-0 updated: build plan change record and tech stack §3 approved; AD-8 locked | User chose to write the build plan change record, then approved | user |
| 2026-10-03 | P-0 closed: index and 4.1 change records approved. P-4 is next | User chose to write them, then approved | user |
| 2026-10-03 | P-4 updated: 4.2 drafted, 16 tasks, then approved with Q1 and Q2 answered; D-16 logged | User chose to draft 4.2, then approved | user |
| 2026-10-03 | Slice 2 section opened; T-2.1 done; D-17 logged | User chose to start slice 2 | user |
