---
doc: dev-log
feature: 003-reminders-and-notifications
title: Reminders and Notifications
stage: 5
status: draft
owner: user
created: 2026-09-23
updated: 2026-09-23
approved_on: null
supersedes: null
---

# Dev Log — Reminders and Notifications

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-set-and-manage.md) · [04.2](./04.2-fire-in-the-app.md)

What actually happened. Deviations from the approved plan are recorded the day
they happen, per rule 5 of the root ruleset.

## Slice 1 — Set and manage

Backend and frontend built 2026-09-23. Verified against a real local
PostgreSQL 16 with a stub Supabase `auth` schema, and in unit and component
tests. **Not yet verified live in a browser** against a real Supabase session
and the real model: see T-1.14 and "Not done, and why".

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-1.1 | Migrations 0016 to 0018 | **done** | Upgrade, downgrade to `0015` and upgrade again all run clean. 0016 gained `repeat_month_day` (D-1); 0018 also extends `capture_turns` (D-5) |
| T-1.2 | `schedule.py` with `next_occurrence` and `describe` | **done** | TC-1.1 to TC-1.12 in `tests/unit/test_schedule.py`. A planner beside it (`schedule_planner.py`) applies FR-2 to FR-4 once for both capture paths |
| T-1.3 | Reminders domain: model, repository, service, five interactors, fakes | **done** | The four planned interactor test files are one file, `test_reminder_interactors.py` (D-9) |
| T-1.4 | Identity service and `public.py` exports | **done** | `get_reminder_settings` returns the defaults when a user has no settings row yet |
| T-1.5 | Capture: `/remind`, `/reminders`, pending `remind_at`, AD-7 clock | **done** | TC-1.14 to TC-1.16 in `test_remind_capture.py`. AD-7 changes task capture too; logged against 001 (T-1.13) |
| T-1.6 | GraphQL: types, queries, mutations, capture union members, schema | **done** | TC-1.19, TC-1.20 in `tests/integration/test_reminders_graphql.py` |
| T-1.7 | Records All tab through `ReminderRecordsPort` | **done** | `records` now returns the union `Task \| Reminder` (D-6) |
| T-1.8 | Codegen, operations, `RemindersStore`, `ToastStore` | **done** | Four operation folders; the fragment lives in `src/fragments/` (D-10). `tsc -b` clean |
| T-1.9 | `Toast`, `Skeleton`, `BusyButton` | **done** | TC-1.22 (`Toast.test.tsx`, 4 cases), TC-1.23 (`BusyButton.test.tsx`, 2 cases) |
| T-1.10 | Capture cards: set, resolved times, question, cap, model down, list | **done** | The resolved-time hints needed a server field (D-2). Component tests in `CommandCenterController.test.tsx` |
| T-1.11 | Reminders tab and All tab with every list state | **done** | Loading, grouped list, empty, error, no match, offline and session ended, each with a test in `RecordsController.test.tsx`. Done and Snooze on rows are slice 2 |
| T-1.12 | Detail, edit, delete with every state | **done** | Detail, loading, not found, invalid, time passed, save failed, deleted while editing, success toast, deleting, delete failed, offline: `ReminderDetailController.test.tsx`, 11 cases |
| T-1.13 | Log AD-7 against 001 in its dev log | **done** | Entry D-44 in `001-capture-and-records-foundation/05-dev-log.md` |
| T-1.14 | Live pass against the real database and model in a browser | **blocked** | This container has no Supabase project to sign in against and its Gemini key is a placeholder. See "Not done, and why" |

### Verification

| Check | Result |
|---|---|
| `pytest -m "not live"` against local PostgreSQL 16 | **210 passed**: 145 unit, 56 integration, 9 settings and logging |
| `pytest -m live` | **2 failed, not run for real**: the Gemini key in this container's `.env` is a placeholder (`API_KEY_INVALID`). Not a code failure; these tests run on a developer machine only, per 04.3 Q4 of epic 001 |
| RLS, TC-1.21 | `test_every_user_table_is_locked_down` covers `reminders`: RLS enabled and forced |
| `mypy app` (strict) | No issues in 176 source files |
| `ruff check .` | Clean |
| `ruff format --check .` | 6 files flagged, all untouched by this slice and already unformatted at `HEAD` (migrations 0008 and 0009, analytics, sign-in tests). Left as they are |
| `alembic downgrade 0015` then `upgrade head` | Clean |
| `npm run codegen`, `tsc -b` | Clean |
| `oxlint` | One warning, pre-existing: unused `StrictMode` import in `main.tsx` |
| `vitest run` | **112 passed** (65 before this slice) |
| `npm run build` | Clean production build |
| Browser pass | Not run. See T-1.14 |

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-1 | `ScheduleSpec` and the `reminders` table carry `repeat_month_day`. The index had the day of the month read from `anchor_local_date` | A reminder "on the 31st" first fires on 30 September, so its anchor is the 30th. Read from the anchor, it would fire on the 30th for ever. The asked-for day has to be stored beside the clamped date for FR-8 to hold | Index §4 corrected, with a change record. Exposed as `repeatMonthDay` on the GraphQL type |
| D-2 | `ReminderDTO.when_note`, and a nullable `whenNote` on the GraphQL `Reminder`, set only on the reminder a create returns | `RemindResolved` shows why a time differs from what was typed ("No time given, so your default reminder time", "7:00 PM has already passed today", "September has 30 days, so the last day"). Only the planner knows which rule applied, and no planned field carried it. One field, computed where the rule is applied, was the smallest route. When two rules apply, a moved day beats a filled-in time | Index §4 corrected. Every read returns `null`; the note is never stored. Unit-tested for all three notes |
| D-3 | `ReminderPort.create_reminder` and `ReminderService.create_reminder` return `ReminderDTO \| ReminderLimitReached \| ReminderNeedsWhen`, not the two members sub-plan §5 names | FR-2's question has to be decided where the schedule is planned, since daily and weekly start today without a date and the other rules cannot. Returning it as an outcome keeps the rule in one place | Index §4 corrected. 04.1 §5 left as approved and superseded by this line |
| D-4 | The GraphQL `Reminder` names its enum `ReminderRepeatKind`, types `origin` as `String!` as `Task` does, and adds `updatedAt` | The pure `RepeatKind` in `schedule.py` is not a GraphQL type, so the GraphQL enum needed its own name, prefixed like `ReminderState`. `Task.origin` is already a string. `updatedAt` matches `Task` | Index §4 corrected |
| D-5 | Migration 0018 also adds the `reminder_created` turn outcome and `capture_turns.resulting_reminder_id` | Without them a `/remind` would be missing from 001's capture history, which logs every turn | History shows a "Reminder set" row. The migration's own docstring names it |
| D-6 | The `records` query returns the union `RecordItem = Task \| Reminder`, not a list of `Task` | FR-26 puts reminders under All. A union keeps each type's own fields and needs no fake common shape | Two existing records integration tests changed to `... on Task`. Frontend `RecordsStore` keeps tasks and the All tab's order; reminders stay only in `RemindersStore`, so there is one copy of each |
| D-7 | `AnswerPendingCapture` returns the full `CaptureResult` union, reminder members included | Answering a `remind_at` question creates a reminder, so the answer can end in any capture outcome | Both capture response handlers switch over the three new members; `assertNever` confirmed nothing else was missed |
| D-8 | The reminder extraction schema and instruction live in `capture/constants.py`, and `GatewayExtractionAdapter` takes an optional `local_clock` that appends "Now is {iso} ({tz})." to every instruction | Reading the sentence is capture's job; `reminders` receives typed fields. The clock is AD-7 applied in the one place every extraction passes | Task capture reads dates in the user's zone too. Logged against 001 as D-44 |
| D-9 | Tests consolidated: one `test_reminder_interactors.py` rather than four files, one `test_remind_capture.py`, and the boundary cases inside `test_reminders_graphql.py` rather than `test_reminders_boundary.py`. Fakes are `fake_user_clock_port.py` and `fake_reminder_records_port.py` in place of the planned settings and local-clock fakes | The four interactors share one fixture set; splitting them would have repeated it four times | Same cases, fewer files. TC ids are cited in each test's docstring |
| D-10 | Frontend: the fragment is `src/fragments/ReminderFields.graphql`, not `src/api/fragments/ReminderFragment.ts` | `src/fragments/` is where codegen reads fragments and where `TaskFields` already lives | None |
| D-11 | Frontend: one `ReminderDetailController` serves both `/records/reminders/:id` and `/records/reminders/:id/edit`, with a `mode` prop. The Reminders tab's `RemindersController` is rendered inside `RecordsController`, which keeps the tabs and the shared search box | Detail and edit share the load, the not-found state and the delete dialog. The tab is one view of the Records page, not a route | Both routes wired in `router.tsx` |
| D-12 | `DeleteConfirmModal` takes a title, message and confirm label instead of a task title and count, and gained busy and failed states. The task detail page passes its old copy | The plan named only "series wording and inline failure"; making the dialog generic was smaller than branching it on record type | Task delete looks and reads exactly as before |
| D-13 | `StoreProvider` accepts an optional `store` prop | Controller tests need to read back what the page wrote to the store (the toast, a removed reminder) | Unused in the app; `App` still creates the store |
| D-14 | Offline, the Reminders tab shows the design's reminder-specific note inside the pane. 001's global offline banner still shows above it | The global banner is rendered by the app shell on every route; suppressing it for one tab would be a special case in the shell | Two offline notices on this one tab. A design follow-up, not a defect |
| D-15 | A `/remind` refused for the cap or because the model is unreadable puts the command back in the bar, and the capture Enter handler now clears the bar **before** submitting | The design's copy says "kept below". Clearing after submitting erased a restore that arrived first; a component test caught it | 001's task refusal card is unchanged |
| D-16 | `RemindAsk`'s three quick answers ("In 1 hour", "This evening, 7:00 PM", "Tomorrow, 9:00 AM") are fixed text sent as the answer and read by the model like typed text | The design draws them as fixed chips | "This evening, 7:00 PM" asked after 7 PM resolves to tomorrow, and the card says so through D-2's note |

### Not done, and why

- **T-1.14, the live browser pass.** The frontend signs in through Supabase and the backend checks that token against Supabase's keys. This container has neither a Supabase project nor a working Gemini key, so the one path that ties them together, `/remind` in a browser, cannot run here. Everything below it is verified: the API against a real database, the UI against mocked operations. Owed before this slice is called done: one pass on a machine with `backend/.env` and `frontend/.env` pointing at the real project.
- **"Change default time" link** on the default-time card (`RemindResolved`). The control it links to arrives in slice 3 (FR-31), so a link now would lead nowhere useful. Added with slice 3.
- **Done and Snooze** on Needs attention rows, and the Needs attention group itself in practice. Nothing fires until slice 2, so no reminder reaches that state yet.

### Incidents and defects

| # | What broke | Cause | Fix |
|---|---|---|---|
| I-1 | A `/remind` refusal's "kept below" command vanished from the bar | Enter cleared the bar after dispatching the submit, so a refusal that restored the command first was overwritten | Clear, then submit (D-15). Caught by a component test before any browser use |
| I-2 | Reverted, not shipped: an earlier `ruff format app tests` run rewrote six files outside this slice | They were already unformatted at `HEAD` | Reverted to keep the diff on this feature. Noted in Verification |

## Slice 2 — Fire in the app

Backend and frontend built 2026-09-23. Verified against a real local
PostgreSQL 16, a real Procrastinate worker, and a real WebSocket, and in unit
and component tests. **Not yet verified live in a browser**: T-2.15 hits the
same missing Supabase project as T-1.14.

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-2.1 | Migration 0019 | **done** | Upgrade, downgrade and upgrade again run clean. The RLS sweep covers all three new tables (TC-2.14). `notifications` carries four more columns than planned (D-18) |
| T-2.2 | `firing.py` pure helpers | **done** | TC-2.1, TC-2.2, TC-2.8 in `test_firing.py`. Also holds the fired and snoozed wording (D-27) |
| T-2.3 | Notifications domain | **done** | TC-2.10 and FR-37's rules in `test_notifications.py` |
| T-2.4 | `fire_due`, `fire_one`, jobs, notifications adapter | **done** | TC-2.3 to TC-2.6, TC-2.9 in `test_fire_reminders.py`. Two idempotent steps, not one transaction (D-17) |
| T-2.5 | Done and Snooze interactors and mutations | **done** | TC-2.7, and TC-2.13 over the wire |
| T-2.6 | Notifications GraphQL | **done** | TC-2.12, TC-2.13 in `test_firing_and_notifications.py` |
| T-2.7 | Listener, WebSocket auth, subscription | **done** | TC-2.15 twice: the listener against a real NOTIFY, and a real WebSocket in `test_notification_subscription.py`, token in `connection_init`, a bad token closed with 4403 |
| T-2.8 | Worker run locally beside the API | **done** | Needed migration 0020 first (D-19). A reminder due 20 s ahead fired 2 s after its time, `on_time`; the next minute's sweep queued nothing |
| T-2.9 | Frontend operations, subscription, `NotificationsStore`, reconnect refetch | **done** | Seven operation folders; the token rides in `connection_init`; a reconnect refetches the count and the list |
| T-2.10 | `PageTopbar` and the bell on five pages; tab title | **done** | TC-2.16 |
| T-2.11 | Notification panel with every state | **done** | TC-2.16: loading, error, empty, list; `PanelActionFailed` copy per action |
| T-2.12 | Pop-up stack and Snooze menu | **done** | TC-2.17, TC-2.18: acting, failed, offline, resulting times |
| T-2.13 | Done and Snooze on Needs attention rows | **done** | TC-2.19, and a failed Done kept on its row |
| T-2.14 | Load check | **done** | TC-2.20, below |
| T-2.15 | Live pass in a browser | **blocked** | As T-1.14: no Supabase project to sign in against in this container |

### Verification

| Check | Result |
|---|---|
| `pytest -m "not live"` against local PostgreSQL 16 | **243 passed**: 170 unit, 64 integration, 9 settings and logging |
| `mypy app` (strict) | No issues in 214 source files |
| `ruff check .` | Clean. `ruff format --check`: the same 6 files as slice 1, untouched |
| `alembic downgrade 0018` then `upgrade head` | Clean, 0019 and 0020 both ways |
| Real worker, `python -m procrastinate ... worker` | One reminder fired on time, unattended (T-2.8) |
| TC-2.20, 2,000 reminders due in one minute across 20 users, local | Default concurrency: all fired, p50 24.7 s, **p95 41.3 s**, max 43.1 s. `--concurrency=10`: p50 16.0 s, **p95 28.5 s**, max 29.7 s. NFR-1 asks for 60 s. Measured, not `estimate`; a hosted database will differ |
| `tsc -b`, `oxlint`, `npm run build` | Clean; oxlint's one warning is still the old `StrictMode` import |
| `vitest run` | **128 passed** (112 after slice 1) |
| Browser pass | Not run. See T-2.15 |

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-17 | `fire_one` is two idempotent steps, not the single transaction 4.2 §5 drew: the firing row and the reminder's new state in one transaction, then the notification published through notifications' service | One transaction would mean passing a `Session` from reminders into notifications, which repo-rules §6.2 forbids. Each step is safe to repeat: the unique firing and the unique notification source keep both to one row. A retry whose first run died between the steps finds the firing already written and publishes it | TC-2.5 and the interrupted-retry unit test cover it. A reminder deleted in that gap loses its notification, the one case not recovered |
| D-18 | `notifications` has `target_id`, `occurred_at`, `action` and `acted_at` beyond build plan §3's fields | Open needs the reminder's id (FR-22); the panel's lines need the due time ("due Sun 6:00 PM, delivered Mon 4:10 PM") and what was done ("marked done 9:41 AM"). Reminders reports Done and Snooze to notifications through its port, so the direction of §2 holds | Build plan §3 is behind the schema by four columns; recorded here rather than reopening the locked build plan |
| D-19 | Migration `0020_procrastinate_schema` installs the job queue's own tables, in a `procrastinate` schema. `core/jobs.py` connects with `search_path=procrastinate` | No migration had ever installed them (002's dev log left the worker unset), so no job could run. A separate schema keeps job rows out of Supabase's exposed `public` schema and out of the RLS sweep. Its triggers name tables unqualified, so any other connection touching them must set the same path | Index §5 gains a migration, with a change record. A Procrastinate upgrade needs its own migration |
| D-20 | The worker runs as `python -m procrastinate --app=app.core.jobs.procrastinate_app worker --concurrency=10`, written into the `Dockerfile`'s comments | The bare `procrastinate` script cannot import `app` from the working directory. Concurrency 10 leaves NFR-1 twice the margin of the default | Deploy config uses this command for the second container (AD-9) |
| D-21 | GraphQL `Settings` exposes `defaultReminderTime`, a slice early | The snooze menu shows "Tomorrow, 9:00 AM" (`ReminderToast`); its control is still slice 3 | Additive |
| D-22 | `NotificationService.publish(*, publish: PublishNotification) -> NotificationDTO \| None`, and a `record_action`, where index §4 listed keyword fields returning a DTO | A DTO over seven keywords; None tells the caller the firing was already published | Index §4 corrected with a change record |
| D-23 | GraphQL names differ from 4.2 §7: the snooze enum is `SnoozeChoice`; `Notification` has `targetId`, `occurredAt`, `action`, `actedAt`; `NotificationMarker.NONE` means on time; mark-all returns `MarkAllNotificationsReadSucceeded { markedCount }`; `Reminder` gains `snoozedUntil`, and its `nextFireAt` is now whichever of series and snooze comes first | The names follow D-18's fields and the existing `ReminderX` naming | 4.2 §7 is superseded by the schema for these names |
| D-24 | `Context.connection_params`, a `SlashitGraphQLRouter` whose `on_ws_connect` verifies the token, and a context getter over `HTTPConnection` | A browser cannot set WebSocket headers; the plan said "context reads the token from `connection_init`" without the mechanism | Tested end to end over a real socket |
| D-25 | Two root fields in one GraphQL document, such as `notifications` and `unreadNotificationCount`, fail: Strawberry resolves them at once on the request's one session | Not new to this slice; this is the first time a test asked for two roots together | The client sends them as separate operations. Every domain shares the limit; a per-resolver session is the fix, a platform change for its own record |
| D-26 | `FakeReminderRepository` and `FakeReminderPort` describe reminders on the test's clock | Slice 1's `test_daily_with_no_date_starts_today` read the wall clock and failed after 20:00 in Kolkata (I-3) | Tests are clock-proof |
| D-27 | A fired reminder's `whenText` reads "Fired today, 7:00 PM" or "Missed, Mon 21 Sep, 7:00 PM"; a snoozed one shows its snooze time | `Main` draws these; slice 1 only had the next occurrence | `summarize_reminder` in `firing.py`, used by the repository |
| D-28 | The Capture page's history control is now a real `<button>` inside `PageTopbar` | It was a clickable `div`; moving it was the moment to fix it | Keyboard reachable |
| D-29 | The Reminders tab does not update live when a reminder fires; it reloads on its next visit | A push carries a notification, not the reminder's new state. The bell, panel and pop-up do update live | Known gap. A second subscription payload, or a refetch on push, would close it |
| D-30 | A failed Done or Snooze on a Reminders row says "That didn't save. Try again." beside it | The design drew row actions but not their failure | Copy not on the canvas; to review |
| D-31 | Mobile artboards `MobileNotifications`, `MobileReminderToast` unmatched, per decision 2. The dark artboards use the existing dark tokens and were not checked by eye | Decision 2 | Owed with a mobile shell and a browser pass |

### Not done, and why

- **T-2.15, the live browser pass**, for T-1.14's reason. The pieces under it are each proven on real infrastructure: the worker, the database, NOTIFY and a real WebSocket.
- **Live refresh of the Reminders tab** on a push (D-29).

### Incidents and defects

| # | What broke | Cause | Fix |
|---|---|---|---|
| I-3 | A slice 1 unit test failed at 21:14 Kolkata time | The fake repository described reminders against the wall clock while the test fixed its own clock | D-26 |
| I-4 | An integration test asking for two root fields raised "A transaction is already begun on this Session" | D-25 | Queries sent apart |
| I-5 | `procrastinate --app=app.core.jobs.procrastinate_app worker` could not load the app | The console script does not put the working directory on `sys.path` | `python -m procrastinate` (D-20) |
| I-6 | The snooze menu's items had names like "Tomorrow9:00 AM" to a screen reader | Two adjacent spans, no separator | `aria-label` "Tomorrow, 9:00 AM"; caught by a test |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-23 | Created. Slice 1 built: 3 migrations, the `reminders` domain, identity and capture extended, records union, 4 frontend operations, 2 stores, 3 shared components, the Reminders tab, detail, edit and delete with every drawn state. 210 backend and 112 frontend tests pass. Live browser pass blocked in this environment | User: "implementation plan approved, start slice 1" | user |
| 2026-09-23 | Slice 2 built: migrations 0019 and 0020, the `notifications` domain, firing, Done and Snooze, the live feed over LISTEN/NOTIFY and a WebSocket, the bell, panel, pop-ups and row actions. 243 backend and 128 frontend tests pass; a real worker fired a reminder; 2,000 due at once fired at p95 28.5 s. Live browser pass blocked in this environment | User: "Proceed", approving 4.2 | user |
