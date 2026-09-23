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

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-set-and-manage.md)

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

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-23 | Created. Slice 1 built: 3 migrations, the `reminders` domain, identity and capture extended, records union, 4 frontend operations, 2 stores, 3 shared components, the Reminders tab, detail, edit and delete with every drawn state. 210 backend and 112 frontend tests pass. Live browser pass blocked in this environment | User: "implementation plan approved, start slice 1" | user |
