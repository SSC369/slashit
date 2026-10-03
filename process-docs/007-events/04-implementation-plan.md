---
doc: implementation-plan
feature: 007-events
title: Events
stage: 4
status: approved
owner: user
created: 2026-10-02
updated: 2026-10-03
approved_on: 2026-10-02
supersedes: null
split: true
---

# Implementation Plan (LLD) — Events

> **Approved** by @user on 2026-10-02. Locked — changes require a change record (§7).

Context: [PRD](./01-prd.md) · [Design](./02-design.md) · [Build plan](./03-build-plan.md)

No code is written before this index and a slice's own sub-plan are approved.

Tables this feature touches, by migration:

| Table | New or changed | Migration | Slice |
|---|---|---|---|
| `calendar_events` | new, with RLS, policy and grants | `NNNN_calendar_events` | 1 |
| `capture_turns` | changed: `resulting_event_id`, outcomes `event_created`, `events_listed` | `NNNN_capture_events` | 1 |
| `pending_captures` | changed: `missing_field` values `event_date`, `event_alert_choice`; `candidate_event` jsonb. `event_alert_choice` is unused from slice 2 and stays in the enum, which cannot drop a value | `NNNN_capture_events` | 1 |
| `events` (analytics) | changed: event types `event_created`, `event_edited`, `event_alert_not_set` | `NNNN_capture_events` | 1 |
| `calendar_events` | changed: `alert_lead_minutes integer` becomes `alert_leads_minutes integer[]`, backfilled | `NNNN_event_alerts` | 2 |
| `reminders` | changed: `event_id`, partial index, many rows per event (build plan AD-8) | `NNNN_event_alerts` | 2 |
| `notifications` | changed: `notification_kind` value `event_alert` | `NNNN_event_alerts` | 2 |

> Migration numbers are taken from the Alembic head on the day each slice is
> built. Epic 006 is being built in parallel and adds its own; whichever lands
> second rebases its `down_revision` onto the other's head. Never two heads.

## 1. Scope recap

Everything in the approved PRD ships, in two slices, per build plan Q4. Slice 1
captures events with `/add-event`, lists them with `/events`, and shows them in
Records and detail with every drawn state. Slice 2 adds alerts, any number per
event, and edit, delete, search and timezone handling.

Slice 1 alone never ships to users: capture accepts "remind me 1 day before" and
would drop it. Both slices go out together; slice 1 is still verifiable end to
end on its own.

## 2. Split decision

| Trigger | Threshold | This feature |
|---|---|---|
| Tasks in the breakdown | more than 15 | about 28, `estimate` |
| Files created or modified | more than 25 | about 60, `estimate` |
| Independently shippable slices | more than one | two |
| Distinct boundaries touched | more than two | six: events, capture, records, reminders, notifications, search |

**Decision:** split into two sub-plans. Sub-plan 2 is drafted after slice 1 is
built, as 003 and 004 did, so it is written against real code.

### Slices

| # | Sub-plan | What works when it lands | Depends on | Status |
|---|---|---|---|---|
| 1 | [04.1-capture-and-browse.md](./04.1-capture-and-browse.md) | `/add-event` saves with every date rule; the two questions and the cap; `/events` grouped by month; Events tab, All tab, detail with all states | none | approved 2026-10-02; built and merged 2026-10-02 (`fb0a767`), T-1.13 and T-1.14 owed. Its FR-16 question and single stored lead are superseded by X-1; slice 2 removes them |
| 2 | `04.2-alerts-and-manage.md` | Any number of alerts per event: set, fire, re-arm yearly and follow edits; FR-16's question removed; edit and delete; search and related; timezone change | 1 | not started |

## 3. File-by-file plan

Each sub-plan lists its own files. Shared across both:

| Path | Change | Slice |
|---|---|---|
| `backend/app/domains/events/` | created: `models.py`, `constants.py`, `public.py`, `jobs.py`, `interfaces/`, `repositories/`, `services/`, `interactors/`, `graphql/`, `adapters/` | 1, 2 |
| `backend/app/domains/events/services/schedule.py` | created | 1 |
| `backend/app/graphql/schema.py` | modified: events queries and mutations | 1, 2 |
| `frontend/src/stores/EventsStore.ts` | created | 1, 2 |
| `frontend/src/fragments/EventFields.graphql` | created | 1 |

## 4. Interfaces and contracts

Contracts crossing the slice boundary. Changing one reopens sub-plan 2.

```python
# events/services/schedule.py, pure, no I/O
@dataclass(frozen=True)
class LocalSchedule:
    start_date: date
    start_time: time | None
    end_date: date | None
    end_time: time | None
    repeat_yearly: bool
    timezone: str

@dataclass(frozen=True)
class Resolved:
    starts_at: datetime        # UTC, next or only occurrence
    ends_at: datetime          # UTC
    occurrence_date: date      # local date of that occurrence

def resolve(s: LocalSchedule, *, now: datetime) -> Resolved: ...
def status(r: Resolved, *, repeat_yearly: bool, now: datetime) -> EventStatus: ...
def normalise_capture(fields: ExtractedEvent, *, local_today: date) -> LocalSchedule: ...
    # FR-4 next occurrence, FR-5 explicit past year kept, FR-7 overnight, FR-10 Feb 29

# events/public.py
class EventService:
    async def create_from_capture(self, *, user_id: UUID, fields: ExtractedEvent,
                                  original_input: str) -> EventCreatedDTO | EventLimitReached
    async def list_upcoming(self, *, user_id: UUID) -> list[EventDTO]
    async def list_for_records(self, *, user_id: UUID) -> list[EventDTO]   # upcoming, then past
    async def get(self, *, user_id: UUID, event_id: UUID) -> EventDTO | None

# reminders/public.py, slice 2 (build plan AD-8)
@dataclass(frozen=True)
class AlertNotSet:
    fire_at: datetime
    reason: Literal["passed", "cap"]

class ReminderService:
    async def set_event_alerts(self, *, user_id: UUID, event_id: UUID, title: str,
                               fire_times: Sequence[datetime], now: datetime) -> list[AlertNotSet]
        # replaces the event's open alert rows; soonest first under the 100 cap
    async def clear_event_alerts(self, *, user_id: UUID, event_id: UUID) -> None
```

`ExtractedEvent` carries `alert_leads_minutes: list[int]`. As built, slice 1
stores the first lead in `alert_lead_minutes` without arming anything, and asks
FR-16's question when there are more. Slice 2, after X-1: every lead is stored,
distinct and ascending (FR-34), in `alert_leads_minutes`, and armed through
`set_event_alerts`. FR-16's question is removed. `EventDTO.alert_lead_minutes`
becomes `alerts: tuple[EventAlertDTO, ...]`, each a lead and its fire time.

```graphql
enum EventStatus { UPCOMING HAPPENING_NOW PAST }
type Event { ... }          # build plan §4, field for field
```

## 5. Data and migrations

`calendar_events` is the build plan's §3 DDL, with these checks added:

```sql
CHECK (char_length(title) BETWEEN 1 AND 200),
CHECK (location IS NULL OR char_length(location) <= 200),
CHECK (description IS NULL OR char_length(description) <= 2000),
CHECK (end_date IS NULL OR end_date >= start_date),
CHECK (start_time IS NOT NULL OR end_time IS NULL),
CHECK (alert_lead_minutes IS NULL OR alert_lead_minutes BETWEEN 0 AND 525600)
```

Slice 2 replaces the last check, in `NNNN_event_alerts`:

```sql
ALTER TABLE calendar_events ADD COLUMN alert_leads_minutes integer[] NOT NULL DEFAULT '{}';
UPDATE calendar_events SET alert_leads_minutes = ARRAY[alert_lead_minutes]
  WHERE alert_lead_minutes IS NOT NULL;
ALTER TABLE calendar_events DROP CONSTRAINT ck_event_alert_lead,
  DROP COLUMN alert_lead_minutes,
  ADD CONSTRAINT ck_event_alert_leads
    CHECK (0 <= ALL (alert_leads_minutes) AND 525600 >= ALL (alert_leads_minutes));
```

Its downgrade restores `alert_lead_minutes` from the first lead and drops the
rest, which loses data and is said so in the migration's docstring. Accepted by the
user on 2026-10-03 over a downgrade that refuses when any event has two leads.

Every migration is reversible except enum additions, which PostgreSQL cannot
drop; their downgrade is a no-op with a comment, as 004's `0027` did.

## 6. State management

`EventsStore` is the store of record for event data (tech stack §3). Capture's
`EventCreated` result, the `/events` result, the records query and detail all
write into it by id. Components read the store, never a query result.

## 7. Error handling

| Failure | Behaviour |
|---|---|
| Model unavailable or quota | 001 FR-35's not-saved card; nothing written |
| Extraction returns no date | FR-2's question, nothing written |
| Extraction returns an end before start on a date range | Treated as overnight when only times differ (FR-7); otherwise the not-saved card asking for a clearer range |
| Cap reached | `EventLimitReached`, drawn refusal, text kept |
| Event read for another user | RLS returns no row; GraphQL answers `null`, drawn as not found |

## 8. Test plan

Feature-level cases. Each sub-plan lists its own.

| Case | Covers |
|---|---|
| User A requests, lists and searches user B's events and gets nothing | T7, NFR-6 |
| `resolve` property test over 1,000 random schedules: `starts_at <= ends_at`, and all-day local dates round-trip in 12 timezones including `Pacific/Kiritimati` and `Pacific/Pago_Pago` | NFR-3 |
| Labelled extraction set of 60 event lines, run live | NFR-2, over 90% of fields |
| Saving card shown on submit, before the request returns; server latency recorded, not gated | NFR-1 |
| An event with three leads at 99 active reminders sets the soonest-firing one and names the other two, reason `cap` | FR-33, AD-8 |

## 9. Rollout

No flag. Both slices merge to `main` together, as 004's did, after slice 2's
definition of done. Deploy runs the migrations, then the worker picks up
`events.roll_yearly` (slice 2).

## 10. Task breakdown

Tasks live in the sub-plans, `T-1.n` and `T-2.n`.

## 11. Definition of done

- Every task in both sub-plans is shipped or explicitly dropped in the dev log.
- Every PRD FR is met and tested; NFR-1 and NFR-2 measured live, or logged as owed with the reason.
- The five feature-level cases in §8 pass.
- The design matches the canvas, or a change record explains why not.
- `index.md` shows 007 as shipped.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-10-02 | Created as the index, two slices | Build plan approved | user |
| 2026-10-02 | Approved | User: "Approve both, start building slice 1" | user |
| 2026-10-02 | NFR-1 test row now the client's saving card, per the PRD change of the same day | Server timing waits on the model, 3.29 s p95 | user |
| 2026-10-03 | Any number of alerts per event (X-1). Slice 2's migration converts `alert_lead_minutes` to `alert_leads_minutes integer[]`; `reminders.event_id` index is no longer unique. §4 adds `set_event_alerts` and `clear_event_alerts`, and `EventDTO.alerts` replaces `alert_lead_minutes`. FR-16's question, built in slice 1, is removed in slice 2. A fifth feature-level case. Re-opened: 4.1's contract for the stored lead, already built, superseded by slice 2; 4.2 not yet drafted | Build plan change approved 2026-10-03. Change approved 2026-10-03, lossy downgrade accepted | user |
