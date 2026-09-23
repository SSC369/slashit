---
doc: implementation-plan
feature: 003-reminders-and-notifications
title: Reminders and Notifications
stage: 4
status: approved
owner: user
created: 2026-09-23
updated: 2026-09-23
approved_on: 2026-09-23
supersedes: null
split: true
---

# Implementation Plan (LLD) — Reminders and Notifications

> **Approved** by @user on 2026-09-23. Locked — changes require a change record (§7).

Context: [PRD](./01-prd.md) · [Design](./02-design.md) · [Build plan](./03-build-plan.md)

No code is written before this index and a slice's own sub-plan are approved.

Tables this feature touches, by migration:

| Table | New or changed | Migration | Slice |
|---|---|---|---|
| `reminders` | new | `0016_reminders` | 1 |
| `user_settings` | changed: four columns | `0017_reminder_settings` | 1 |
| `pending_captures` | changed: enum value `remind_at` | `0018_pending_capture_remind` | 1 |
| `reminder_firings`, `notifications`, `notification_deliveries` | new | `0019_firings_and_notifications` | 2 |
| `reminders` | changed: `snoozed_until` | `0019_firings_and_notifications` | 2 |
| Procrastinate's queue tables, schema `procrastinate` | new | `0020_procrastinate_schema` | 2 |
| `notifications` | changed: `time_zone` | `0021_notification_time_zone` | 3 |

## 1. Scope recap

Everything in the approved PRD ships, in four slices. Slice 1 lets a user set,
see, edit and delete reminders, and fixes capture's UTC dates for tasks too.
Slices 2 to 4 make reminders fire in the app, then by email, then hold up across
timezone moves and outages.

## 2. Split decision

| Trigger | Threshold | This feature |
|---|---|---|
| Tasks in the breakdown | more than 15 | about 55, `estimate` |
| Files created or modified | more than 25 | about 120, `estimate` |
| Independently shippable slices | more than one | four |
| Distinct boundaries touched | more than two | five: capture, reminders, notifications, records, identity, plus the worker |
| Length of the drafted plan | more than 500 lines | over, as one document |

**Decision:** split into four sub-plans.

> Assumption: the four-slice order below, calling Resend with `httpx` (already
> installed, `requirements.txt`) rather than its SDK, and drafting sub-plans 2
> to 4 only as the slice before each lands. These were offered as questions on
> 2026-09-23 and the prompt was declined, so each is the recommended option.
> Strike any in review.

### Slices

| # | Sub-plan | What works when it lands | Depends on | Status |
|---|---|---|---|---|
| 1 | [04.1-set-and-manage.md](./04.1-set-and-manage.md) | `/remind` sets a reminder in the user's timezone; `/reminders` lists them; the Reminders tab, detail, edit and delete work, with every drawn state. Task dates read in the user's timezone | — | approved, built 2026-09-23; live pass owed |
| 2 | [04.2-fire-in-the-app.md](./04.2-fire-in-the-app.md) | A due reminder fires within a minute: the bell counts it, the panel lists it, an open app pops it up; Done and Snooze work; late and missed are marked | 1 | approved, built 2026-09-23; live pass owed |
| 3 | [04.3-email-and-settings.md](./04.3-email-and-settings.md) | Reminders also arrive by email; the default time and both switches work in Settings; the email cap and both-off warning hold | 2 | built; T-3.10 waits on a sending domain |
| 4 | 04.4-timezone-and-hardening.md | A timezone change moves recurring reminders; the reconciliation alert and 90-day purge run | 2 | not started |

Slices 3 and 4 are independent of each other and can be built in either order.

## 4. Interfaces and contracts

Only what crosses a slice boundary. Python signatures are keyword-only, per
`backend/.claude/rules/code-rules.md`.

### Schedule maths, created in slice 1, used by 2 and 4

```python
# app/domains/reminders/services/schedule.py — pure, no I/O
class RepeatKind(StrEnum): NONE, DAILY, WEEKLY, MONTHLY, YEARLY

@dataclass(frozen=True)
class ScheduleSpec:
    repeat_kind: RepeatKind
    repeat_interval: int            # 1 or more; ignored for NONE
    repeat_weekdays: tuple[int, ...]  # 0=Mon..6=Sun; WEEKLY only, non-empty
    repeat_month_day: int | None    # MONTHLY/YEARLY: the day asked for, kept past a clamp (FR-8)
    local_time: time                # minute precision
    anchor_local_date: date         # first occurrence; yearly month comes from it
    one_time_at: datetime | None    # NONE only, UTC instant (FR-11)

def next_occurrence(*, spec: ScheduleSpec, timezone: ZoneInfo, after: datetime) -> datetime | None
def describe(*, spec: ScheduleSpec, timezone: ZoneInfo, now: datetime) -> ScheduleSummary
# ScheduleSummary: when_text "Tomorrow, 7:00 PM", repeat_text "Every weekday" (FR-5)
```

`next_occurrence` owns FR-8 (month end, February 29), FR-9 and AD-12 (clock
changes). Slice 2's firing job and slice 4's recompute call it and nothing else.

### Published services

```python
# reminders/public.py — slice 1 creates, slice 2 adds fire_due and act
ReminderDTO(id, user_id, description, spec: ScheduleSpec, schedule_timezone: str,
            next_fire_at: datetime | None, state: ReminderState, last_fired_at, last_action,
            summary: ScheduleSummary, origin, original_input, created_at, updated_at,
            when_note: str | None = None)   # set only on the DTO a create returns
ReminderService.create_reminder(*, user_id, fields: ReminderFields, origin, original_input) -> ReminderDTO | ReminderLimitReached | ReminderNeedsWhen
ReminderService.list_active(*, user_id) -> list[ReminderDTO]
ReminderService.list_for_records(*, user_id, search: str | None) -> list[ReminderDTO]

# identity/public.py — slice 1 creates
ReminderSettingsDTO(timezone: str, default_reminder_time: time, popups_enabled: bool,
                    email_enabled: bool, channels_off_warned_at: datetime | None)
IdentityService.get_reminder_settings(*, user_id) -> ReminderSettingsDTO
IdentityService.get_account_email(*, user_id) -> str | None   # slice 3

# notifications/public.py — slice 2 creates, slice 3 adds email delivery
NotificationService.publish(*, publish: PublishNotification) -> NotificationDTO | None  # None: already published
NotificationService.record_action(*, user_id, source_id, action, acted_at) -> None
```

### Live signal, slice 2

```text
channel:  slashit_notifications
payload:  {"user_id": "<uuid>", "notification_id": "<uuid>"}   ids only, never text
sent:     after the transaction that wrote the notification commits
```

### Job names

| Job | Slice | Runs |
|---|---|---|
| `reminders.fire_due` | 2 | every minute; defers one `fire_one` per due reminder |
| `reminders.fire_one(reminder_id, scheduled_for)` | 2 | per due reminder, queueing lock `fire:{reminder_id}:{scheduled_for}`, retried |
| `notifications.send_email(delivery_id)` | 3 | per delivery, 5 retries |
| `reminders.timezone_changed(user_id)` | 4 | deferred by identity, by name |
| `reminders.reconcile` | 4 | hourly |
| `notifications.purge_old` | 4 | daily |

### GraphQL `Reminder` type, slice 1, extended by 2

```graphql
type Reminder {
  id: ID!  description: String!  state: ReminderState!      # UPCOMING | FIRED | DONE
  nextFireAt: DateTime  whenText: String!  repeatText: String!
  repeatKind: ReminderRepeatKind!  repeatInterval: Int!  repeatWeekdays: [Int!]!
  repeatMonthDay: Int  localTime: String!  anchorLocalDate: Date!  scheduleTimezone: String!
  lastFiredAt: DateTime  lastAction: ReminderAction           # slice 2 fills these
  origin: String!  originalInput: String  createdAt: DateTime!  updatedAt: DateTime!
  whenNote: String                                             # only on the create response
}
```

## 5. Data and migrations

| Migration | Change | Reversible | Backfill | Slice |
|---|---|---|---|---|
| `0016_reminders` | Create `reminders`, build plan §3 fields; index `(next_fire_at) WHERE deleted_at IS NULL AND state <> 'done'`; RLS enabled and forced, owner policy, grant to `authenticated` | yes | none | 1 |
| `0017_reminder_settings` | `user_settings` gains `default_reminder_time time NOT NULL DEFAULT '09:00'`, `popups_enabled bool DEFAULT true`, `email_enabled bool DEFAULT true`, `channels_off_warned_at timestamptz NULL` | yes | defaults fill existing rows | 1 |
| `0018_pending_capture_remind` | `ALTER TYPE pending_capture_missing_field ADD VALUE 'remind_at'`; `known_title` is reused for the reminder text | no: PostgreSQL cannot drop an enum value; downgrade leaves it | none | 1 |
| `0019_firings_and_notifications` | Create `reminder_firings`, `notifications`, `notification_deliveries` with the three unique constraints of build plan §3, RLS and grants. `reminders` gains `snoozed_until timestamptz NULL` and a partial index on it | yes | none | 2 |
| `0020_procrastinate_schema` | Install the job queue's tables in a `procrastinate` schema; jobs connect with that search path | yes | none | 2 |
| `0021_notification_time_zone` | `notifications` gains `time_zone text NOT NULL DEFAULT 'UTC'`, the reminder's zone for the email (04.3 decision 3) | yes | default fills existing rows | 3 |

## 6. State management

| State | Lives in | Lifetime | Invalidated by |
|---|---|---|---|
| Reminders list and detail | `RemindersStore` (MobX), slice 1 | Session | Every reminder mutation's response handler; slice 2's subscription payload |
| Success toast | `ToastStore`, slice 1 | 4 s, or until closed | A newer toast |
| Notifications page and unread count | `NotificationsStore`, slice 2 | Session | Subscription payload; refetch on WebSocket reconnect; read mutations |
| Open pop-ups | `NotificationsStore.popups`, slice 2 | Until acted on or closed | Done, Snooze, close |
| Reminder settings | `SettingsStore`, extended in slice 3 | Session | `updateReminderSettings` |
| Schedule and state of a reminder | `reminders` row | Row lifetime | Create, edit, done, snooze, sweep, timezone recompute |

No Apollo cache is read by a component. Operations run `network-only` and write
into the store, per `frontend/rules/repo-rules.md` §7.

## 8. Test plan: cases spanning slices

| id | Level | Case | Covers |
|---|---|---|---|
| X-1 | integration | `/remind Call Mom tomorrow at 7pm` for a user in Asia/Kolkata fires once at 19:00 local the next day: one firing row, one notification, one email delivery | FR-1, FR-9, FR-12, FR-14, FR-16 |
| X-2 | integration | A weekly reminder edited to Monday only never fires on Tuesday again | FR-28, FR-30 |
| X-3 | integration | A deleted reminder due in the same minute as the sweep does not fire | FR-30 |
| X-4 | integration | Two sweeps running at once over the same due reminder defer one `fire_one` job, and running `fire_one` twice produces one firing | FR-16, NFR-3, AD-2 |
| X-7 | integration | 2,000 reminders due at 09:00 all fire with p95 delay under 60 s on the deployed worker concurrency | NFR-1, AD-2 |
| X-5 | integration | User A cannot read, edit, snooze, delete or receive user B's reminder or notification, over HTTP or the subscription | NFR-6, T7 |
| X-6 | integration | A timezone change from Asia/Kolkata to Europe/London keeps a daily 7 PM at 7 PM London and a one-time reminder at its instant | FR-10, FR-11 |

## 9. Rollout

| Item | Decision |
|---|---|
| Feature flag | None. There are no outside users yet |
| Rollout stages | Each slice merges when its definition of done holds. The worker container is deployed with slice 2 |
| Kill switch | `REMINDERS_FIRING_ENABLED=false` stops the sweep; `REMINDER_EMAIL_ENABLED=false` stops Resend calls, leaving the list working. Both read from `core/settings.py` |
| Metrics to watch | Firing delay p95 (NFR-1), duplicates (NFR-3), reconciliation errors (NFR-4), email failures, bounces and complaints |
| Rollback plan | Revert the slice. Migrations 0016, 0017 and 0019 downgrade; 0018 leaves one unused enum value |

## 11. Definition of done

- [ ] All four sub-plans done, every task shipped or dropped in the dev log by id.
- [ ] Cross-slice cases X-1 to X-6 pass against a real database.
- [ ] Every artboard on the design canvas matched, or a change record says why not.
- [ ] Firing delay, duplicates, reconciliation and email outcomes are logged (PRD §8).
- [ ] 001's dev log records AD-7's change to task date reading.
- [ ] `index.md` shows 003 as `shipped`.

## Change log

| Date | Change | Why | Approved by | Sub-plans re-opened |
|---|---|---|---|---|
| 2026-09-23 | Created with sub-plan 1 | Build plan approved | user | none |
| 2026-09-23 | Job table and cross-slice tests follow the build plan's amended AD-2: `fire_due` fans out one `fire_one` job per due reminder. X-4 reworded, X-7 added | Build plan change record, same day | user | none: sub-plan 2 is not yet written; 4.1 does not touch firing |
| 2026-09-23 | Approved | User: "implementation plan approved, start slice 1" | user | none |
| 2026-09-23 | §4 brought in line with slice 1 as built: `ScheduleSpec.repeat_month_day`; `ReminderDTO.when_note` and the GraphQL `whenNote`; `create_reminder` also returns `ReminderNeedsWhen`; the GraphQL type adds `repeatMonthDay` and `updatedAt`, names its enum `ReminderRepeatKind` and types `origin` as `String`, as `Task` does | Found while building slice 1; each is logged in `05-dev-log.md` (D-1 to D-4) | user, with slice 1's commit | none: sub-plans 2 to 4 are not yet written |
| 2026-09-23 | `reminders.snoozed_until` added to migration 0019 and the table list | User chose, before 04.2 was drafted, that snoozing a recurring reminder adds a one-off firing and leaves the series alone (FR-21 with FR-24) | user, with 04.2 | 4.2 only; 4.1 is built and unaffected |
| 2026-09-23 | §4 `NotificationService` signatures and §5 migration `0020_procrastinate_schema` brought in line with slice 2 as built | Dev log D-19 and D-22 | pending user review | none: 4.3 and 4.4 are not yet written |
| 2026-09-23 | Migration `0021_notification_time_zone` added to the table list and §5 | 04.3 decision 3: the email job reads the reminder's zone from the notification, since notifications may not call reminders | user, with 04.3 | 4.3 only |
| 2026-09-23 | §4 `IdentityService.get_account_email` returns `str \| None` | Built with slice 3: an account may have no address, and 4.3 §8 plans for it. Dev log D-33 | pending user review | none: 4.3 is built to it; 4.4 does not use it |
