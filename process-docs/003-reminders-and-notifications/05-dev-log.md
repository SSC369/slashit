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

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-set-and-manage.md) · [04.2](./04.2-fire-in-the-app.md) · [04.3](./04.3-email-and-settings.md) · [04.4](./04.4-timezone-and-hardening.md)

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

## Slice 3 — Email and settings

Backend and frontend built 2026-09-23. Verified against a real local
PostgreSQL 16, in unit, integration and component tests. Email ships switched
off (decision 2): **no real email has been sent**. T-3.10 waits on a verified
sending domain and a Resend key, and the browser pass waits on T-1.14's
Supabase project.

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-3.1 | Migration 0021; settings variables | **done** | Downgrade to 0020 and upgrade to head run clean. Settings refuses email switched on without a key and a sender (D-35) |
| T-3.2 | Identity: save settings, warning stamp, account email; `updateReminderSettings` | **done** | TC-3.6, TC-3.7 in `test_reminder_settings.py`; TC-3.9 in `test_reminder_email_and_settings.py` |
| T-3.3 | `email_content.py` | **done** | TC-3.1: subject, time in the reminder's zone, the late line, link, footer, user text escaped |
| T-3.4 | Email decision, cap and paused notice in `publish` | **done** | TC-3.2, TC-3.3, TC-3.4 in `test_reminder_email.py`. A firing with email disabled by configuration logs `notifications.email_disabled` (§8) |
| T-3.5 | `resend_sender.py`, `email_queue.py`, `send_email` job | **done** | TC-3.5 unit; TC-3.8 integration: two fires, one queued delivery, sent once to the account's real `auth.users` address through a fake sender, then `skipped` on a repeat |
| T-3.6 | Frontend Settings section and `Switch` | **done** | TC-3.10: loading, the saved values, spinner beside the control, failure flips back, both-off warning, a refused time |
| T-3.7 | `email_paused` notice in the panel | **done** | TC-3.11: title, detail, no Done, Snooze or Open |
| T-3.8 | Return to the link after sign-in | **done** | TC-3.12, email and Google. Logged against 002 (D-39) |
| T-3.9 | "Change default time" link on the capture card | **done** | Asserted in the capture test; links to `/settings` (D-40) |
| T-3.10 | Real send, once a domain and key exist | **waiting** | No sending domain or key exists (build plan Q9). Set `REMINDER_EMAIL_ENABLED`, `RESEND_API_KEY`, `REMINDER_EMAIL_FROM`, `APP_BASE_URL`, fire one reminder, and record the email here |

### Verification

| Check | Result |
|---|---|
| `pytest -m "not live"` against local PostgreSQL 16 | **260 passed**: 185 unit, 66 integration, 9 settings and logging |
| `mypy app` (strict) | No issues in 221 source files. `mypy app tests` shows the 3 errors a clean `HEAD` shows, in files not touched |
| `ruff check .` | Clean. `ruff format --check`: every changed file formatted; the same 6 old files are not |
| `alembic downgrade 0020_procrastinate_schema` then `upgrade head` | Clean |
| `tsc -b`, `oxlint`, `npm run build` | Clean; oxlint's one warning is still the old `StrictMode` import |
| `vitest run` | **147 passed** (128 after slice 2) |
| Real email | Not sent. See T-3.10 |
| Browser pass | Not run. See T-1.14 |

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-32 | Names differ from 4.3 §6 and §7. The sender port is `EmailSenderPort`, which raises `EmailSendError`; a further `EmailQueuePort.enqueue_email` wraps the queue. Repository methods are `get_email_delivery`, `mark_email_sent`, `record_email_failure` and `get_email_status_for_source`, where §6 listed `get_delivery`, `mark_delivery_sent` and `record_delivery_attempt` | Each touches only the email delivery, so the name says email. The queue port lets `publish` be unit-tested without the job queue | 4.3 §6 and §7 are superseded by the code for these names |
| D-33 | `IdentityService.get_account_email` returns `str \| None`; index §4 has `str`. `IdentityService` takes `auth_account_repository` as an optional collaborator | §8 plans for "No account email", which needs None. Only the email job needs the repository, so the other builders are unchanged | Index §4 is behind by `\| None`. The job marks the delivery `failed` and logs `no_address` |
| D-34 | `PublishNotification.source_id` is optional and gains `time_zone`; `NotificationDTO` gains `time_zone`. `insert_notification` returns `PublishedNotification`: the notification, its email delivery id and status. The `email_paused` notice goes through the same insert, with no source, pop-up and email both `skipped` | One write path for every list row. The notice has no firing behind it, so no source; it must never email about email | `publish` still returns `NotificationDTO \| None`, so reminders is unchanged apart from passing the zone |
| D-35 | Settings refuses to start when `REMINDER_EMAIL_ENABLED` is true and `RESEND_API_KEY` or `REMINDER_EMAIL_FROM` is empty. The key joins the log redactor's secrets | A missing key found at boot costs one restart. Found at send time, it costs five failed attempts per email | Not in 4.3; additive |
| D-36 | The default time is a list of half-hour steps, plus the saved time when it falls between steps | The artboard draws a dropdown showing 9:00 AM and no step | > Assumption: half-hour steps. A time typed in capture is not limited to them |
| D-37 | Copy not on the canvas: "Couldn't turn pop-ups off. They are still on. Try again.", "Couldn't change the default time. It is still 9:00 AM. Try again.", and "Sent to your account email, at most 50 a day" while the address has not loaded | `SettingsFailed` draws only the email line. The others follow its pattern | To review with the design |
| D-38 | The both-off warning shows after the save that returns `showBothOffWarning`, and hides as soon as either switch is back on | FR-34 warns once, and the server stamps that once. A warning left up after a switch is back on would be false | Reloading the page does not show it again, by design |
| D-39 | Return-to rides a `?next=` parameter on `/sign-in`. Only a path on this origin is honoured | Decision 1. Checking the path keeps the parameter from becoming an open redirect | Supabase's Redirect URLs must allow paths under the site URL (`/**`), or Google lands on the site root. Logged in 002's dev log |
| D-40 | The capture card shows "Change default time" when `whenNote` is the server's default-time sentence | No field says which rule wrote the note (D-2), and adding one for a link was more than the link is worth | A change to that sentence in `schedule_planner.py` must change `DEFAULT_TIME_NOTE` in `ReminderCards.tsx` too |
| D-41 | The `email_paused` notice uses the `MailX` icon | The artboard's icon was not matched glyph for glyph | Visual only |

### Not done, and why

- **T-3.10, the first real email.** No verified sending domain or Resend key exists. Everything up to the provider call is tested; the call itself is tested against a fake.
- **The browser pass**, for T-1.14's reason.
- **Resend bounce and complaint webhooks.** Out of this slice by 4.3 §3; they need a deployed public URL.
- **`DarkSettingsReminders`** uses the existing dark tokens and was not checked by eye (D-31).

### Incidents and defects

| # | What broke | Cause | Fix |
|---|---|---|---|
| I-7 | `ruff format app` reformatted three old files outside this slice | The command was run on the whole folder | Reverted with `git checkout`; only changed files are formatted |
| I-8 | `mypy` flagged the purge test's fake as not an `AuthAccountRepository` | The Protocol gained `get_email` | The fake gained it too |

## Slice 4 — Timezone and hardening

Backend and frontend built 2026-09-23. Verified against a real local
PostgreSQL 16 and a real Procrastinate worker, in unit, integration and
component tests. This is the last slice; what the feature still owes is under
"What the feature still owes".

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-4.1 | Migration 0022; notification reads skip deleted rows | **done** | Downgrade to 0021 and upgrade to head run clean. List, count, get, mark read, mark all read and Done's stamp skip deleted rows. One more index than planned (D-45) |
| T-4.2 | Purge interactor and daily job | **done** | TC-4.8 in memory and against the database: 91 days stamped and kept, 89 days listed |
| T-4.3 | Rezone repository method and interactor | **done** | TC-4.1 to TC-4.3, including a daylight-saving change in New York and a firing landing mid-move (D-43) |
| T-4.4 | Identity's queue port, `updateTimezone`, the `timezone_changed` job | **done** | TC-4.4; TC-4.7 and TC-4.9 over the API with the real queue |
| T-4.5 | Reconcile interactor and hourly job | **done** | TC-4.5: 6 minutes overdue logs `reminders.lost`, 4 minutes does not; no reminder text in the log |
| T-4.6 | `REMINDERS_FIRING_ENABLED` | **done** | TC-4.6. Default true |
| T-4.7 | Timezone note sentence | **done** | TC-4.11 |
| T-4.8 | Cross-slice cases X-1, X-2, X-5 | **done** | X-1 and X-2 new in `test_timezone_and_hardening.py`; X-5 cited from existing tests (D-48) |
| T-4.9 | Worker run | **done** | All four periodic jobs registered. A daily 7 PM Kolkata reminder moved to 7 PM London 1 s after `updateTimezone`, by the worker. `reconcile` and `purge_old` each ran once on it: 0 lost, 0 purged |

### Verification

| Check | Result |
|---|---|
| `pytest -m "not live"` against local PostgreSQL 16 | **276 passed**: 196 unit, 71 integration, 9 settings and logging |
| `mypy app tests` | The same 3 errors a clean `HEAD` shows, in files not touched; `app` alone is clean |
| `ruff check .` | Clean. Every changed file formatted |
| `alembic downgrade 0021_notification_time_zone` then `upgrade head` | Clean |
| Real worker | T-4.9 above |
| `tsc -b`, `oxlint`, `npm run build` | Clean; oxlint's one warning is still the old `StrictMode` import |
| `vitest run` | **148 passed** (147 after slice 3) |

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-42 | No `list_live_for_rezone` or `select_overdue`, which 4.4 §8 listed. The rezone reads `list_for_user` and keeps what is not done and not yet in the new zone; reconcile calls `select_due` with a cutoff 5 minutes back. `RezoneWrite` carries the whole spec | The existing methods already return exactly those rows. Two methods that only forward would be ceremony | Two fewer repository methods |
| D-43 | The rezone re-reads and retries, up to 3 passes, when a reminder changed between its read and its write; `reminders.rezone_incomplete` is logged if any are still in the old zone | A firing bumps `updated_at`. Without a retry, a reminder firing at that moment would stay in the old zone for good. An edit made meanwhile still wins: it was saved in the new zone, so the re-read skips it | TC-4.3 covers both |
| D-44 | `reminders.lost` logs the reminder id, due time and minutes overdue, not the user id 4.4 §6 listed | The due-row DTO the sweep uses carries no user id, and the reminder id finds it | Minor |
| D-45 | Migration 0022 also adds `ix_notifications_live_created`, a partial index on `created_at` for live rows | Without it the daily purge scans the whole table | Additive |
| D-46 | The email cap's counts and a firing's email status still read soft-deleted rows | Both look at today or at one firing; a row older than 90 days never matters to either | None |
| D-47 | `tests/conftest.py` gains a `job_queue` fixture, and 002's `updateTimezone` integration test uses it | The mutation now defers a job, and the test client does not run the API's lifespan, which opens the queue | An API process must open the queue at start, as `main.py` already does |
| D-48 | X-1 starts from the fields capture yields, not from typing the `/remind` sentence; X-5 is cited, not re-tested | Reading the sentence needs the model, and slice 1's `test_remind_capture.py` covers it. X-5's isolation is already tested over HTTP, the panel and the WebSocket | The index's X-1 to X-6 all run against a real database |
| D-49 | `updateTimezone` reads the stored settings before saving, and announces the change only when the zone differs, or when no settings row existed | Saving the same zone must not queue a move (TC-4.4) | One extra read per timezone save |
| D-50 | The timezone note keeps "Dates already recorded stay exactly as they are." and adds decision 3's two sentences after it | Decision 3 was to add, not replace | Copy not on the canvas; to review |

### Incidents and defects

| # | What broke | Cause | Fix |
|---|---|---|---|
| I-9 | `ruff format app`, and later `ruff format tests/fakes`, reformatted five old files outside this slice | I-7 again: formatting a folder instead of the changed files | Reverted with `git checkout`. Format changed files by name only |
| I-10 | 43 integration tests failed to connect mid-session | The local PostgreSQL had stopped | Restarted; the suite passed |
| I-11 | 002's `updateTimezone` integration test failed with `AppNotOpen` | D-47 | The `job_queue` fixture |

## What the feature still owes

All four slices are built. The index's definition of done, checked 2026-09-23:

| Item | State |
|---|---|
| Every task shipped or dropped | Shipped, except T-1.14, T-2.15 and T-3.10 |
| X-1 to X-6 against a real database | **Pass.** X-7 measured in slice 2 |
| Every artboard matched | Not confirmed. No browser pass has run; mobile and dark artboards are unchecked (D-31) |
| Firing delay, duplicates, reconciliation and email outcomes logged | **Yes**: `reminders.fire_one` delay, the unique constraints, `reminders.lost`, `notifications.email_*` |
| 001's dev log records AD-7 | **Yes**, as 001's D-44 (see D-8) |
| `index.md` shows `shipped` | **No.** Blocked on the three items below |

| Owed | Blocked on |
|---|---|
| T-1.14, T-2.15: live browser passes, with the artboard check | A Supabase project reachable from the test environment, and a model key |
| T-3.10: first real email | A verified sending domain and a Resend key |
| Supabase Redirect URLs allow paths under the site URL (D-39) | Dashboard access |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-23 | Created. Slice 1 built: 3 migrations, the `reminders` domain, identity and capture extended, records union, 4 frontend operations, 2 stores, 3 shared components, the Reminders tab, detail, edit and delete with every drawn state. 210 backend and 112 frontend tests pass. Live browser pass blocked in this environment | User: "implementation plan approved, start slice 1" | user |
| 2026-09-23 | Slice 2 built: migrations 0019 and 0020, the `notifications` domain, firing, Done and Snooze, the live feed over LISTEN/NOTIFY and a WebSocket, the bell, panel, pop-ups and row actions. 243 backend and 128 frontend tests pass; a real worker fired a reminder; 2,000 due at once fired at p95 28.5 s. Live browser pass blocked in this environment | User: "Proceed", approving 4.2 | user |
| 2026-09-23 | Slice 3 built: migration 0021, email delivery with its daily cap and paused notice, the `send_email` job, `updateReminderSettings`, the Settings reminders section with every drawn state, the `email_paused` notice, return to the link after sign-in, and the "Change default time" link. 260 backend and 147 frontend tests pass. Email ships off; the first real send (T-3.10) waits on a sending domain | User: "Commit and proceed with next", approving 4.3 | user |
| 2026-09-23 | Slice 4 built: migration 0022, timezone moves through `reminders.timezone_changed`, hourly reconciliation, the 90-day soft delete, the firing kill switch, and cross-slice cases X-1 and X-2. 276 backend and 148 frontend tests pass; a real worker moved a reminder from Kolkata to London time. The feature's definition of done is checked; three live checks remain owed | User: "1", approving 4.4 | user |
