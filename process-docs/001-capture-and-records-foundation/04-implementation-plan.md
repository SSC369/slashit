---
doc: implementation-plan
feature: 001-capture-and-records-foundation
title: Capture and Records Foundation
stage: 4
status: approved
owner: user
created: 2026-09-13
updated: 2026-09-19
approved_on: 2026-09-13
supersedes: null
split: true
---

# Implementation Plan (LLD) — Capture and Records Foundation

> **Approved** by @user on 2026-09-13. Locked — changes require a change record (§7 of the rules).

Context: [PRD](./01-prd.md) · [Design](./02-design.md) · [Build plan](./03-build-plan.md)

The index is approved: the slicing, order and cross-slice contracts are locked.
Each sub-plan is still approved on its own before its own build starts, per §6
of the process rules.

## Tables touched

| Table | Change | Slice |
|---|---|---|
| `tasks` | new | 1 |
| `pending_captures` | new | 1 |
| `user_settings` | new | 2 |
| `capture_turns` | new | 4 |
| `tasks` | changed: `deleted_at` added, soft delete | metrics gap closure, 2026-09-19 |
| `events` | new | metrics gap closure, 2026-09-19 |

## 1. Scope recap

Ships: commands-only capture into tasks, the records view for tasks, timezone
settings, the installed-app surfaces, and dark theme. Waits: every record type
past tasks, plain-language capture, cross-tab live sync, and any expiry on an
unanswered question — all deferred by the build plan or the PRD's own scope.

## 2. Split decision

| Trigger | Threshold | This feature |
|---|---|---|
| Tasks in the breakdown | more than 15 | ~28 across three slices |
| Files created or modified | more than 25 | ~55 |
| Independently shippable slices | more than one | 3 |
| Distinct boundaries touched | more than two | 4: data model, capture pipeline, records surface, installed-app/theme |
| Length of the drafted plan | more than 500 lines | Would be, undivided |

**Decision: split into 3 sub-plans, a 4th added 2026-09-14 for capture history
and loading feedback (FR-44 to FR-46).** Small enough on its own (one table,
one query, three UI touch-ups) that it would not have crossed the split
thresholds by itself; it is sliced anyway to match the other three and because
it depends on both.

### Slices

| # | Sub-plan | What works when it lands | Depends on | Status |
|---|---|---|---|---|
| 1 | [04.1-capture-core.md](./04.1-capture-core.md) | Type a command in the Command Center and get a task, a question, or an honest refusal. Every capture outcome in the design's four flows | — | draft |
| 2 | [04.2-records-and-settings.md](./04.2-records-and-settings.md) | Open Records, see every task, filter, search, open one, edit or delete it. Change timezone in Settings | 1 | not started |
| 3 | [04.3-installed-app-and-theme.md](./04.3-installed-app-and-theme.md) | Install Slashit to a home screen, read records offline, get told when an update is ready. The app follows the device's light or dark setting everywhere | 2 | approved |
| 4 | [04.4-chat-history-and-loading-feedback.md](./04.4-chat-history-and-loading-feedback.md) | Open a history panel from Capture and see every past turn. Saving the task edit form and answering a pending question both show a loading state instead of nothing | 1, 2 | approved |

Slice 1 is capture without a way to browse what was captured, which is
demonstrable but incomplete on its own; slice 2 is what makes it a product.
Slice 3 is additive polish that touches no domain logic, which is why it comes
last and depends only on the UI slice 2 finishes. Slice 4, added 2026-09-14
per FR-44 to FR-46, is the same kind of polish: it adds one table and one
query to capture, and a loading affordance to interactions slices 1 and 2
already built. It depends on both because it puts a spinner on slice 2's
task edit and completion, and logs slice 1's capture turns.

## 3. File-by-file plan

Moved to the sub-plans. Slice order is section 2.

## 4. Interfaces and contracts

Only what crosses a **slice** boundary. Internal shapes live in each sub-plan.

### The `Task` GraphQL type and DTO, slice 1 to slice 2

Slice 1 creates it (`TaskCreated` carries one). Slice 2 is the first to query,
edit and delete it. The shape does not change between them.

```python
# app/domains/records/interfaces/dtos.py
@dataclass(frozen=True)
class TaskDTO:
    id: UUID
    user_id: UUID
    title: str
    due_at: datetime | None
    status: Literal["pending", "done"]
    is_overdue: bool          # computed in the repository query, build plan §3
    origin: Literal["command", "edit"]
    original_input: str | None
    created_at: datetime
    updated_at: datetime
```

```graphql
type Task {
  id: ID!
  title: String!
  dueAt: DateTime
  status: TaskStatus!
  isOverdue: Boolean!
  origin: RecordOrigin!
  originalInput: String
  createdAt: DateTime!
  updatedAt: DateTime!
}
```

### The port `capture` depends on, to reach `records`

Per backend repo-rules.md §6: the consumer (`capture`) declares the port in its
own words, the provider (`records`) publishes a service, the consumer's adapter
joins them. This crosses from slice 1 (which builds and calls it) toward slice
2 (which builds the rest of `records` behind the same published service).

```python
# app/domains/capture/interfaces/ports.py — capture's own vocabulary
class TaskCreationPort(Protocol):
    async def create_task(self, *, user_id: UUID, title: str, due_at: datetime | None,
                           origin: str, original_input: str) -> TaskDTO: ...

# app/domains/records/public.py — records' published surface
__all__ = ["RecordsService", "TaskDTO"]
```

Slice 1 builds only as much of `RecordsService` as creation needs. Slice 2
extends the same class; it does not create a second one.

### The `CaptureResult` union, fixed by the build plan §7

All ten members are slice 1's contract with the frontend. Slice 2 and 3 do not
add members to it.

## 5. Data and migrations

| Migration | Change | Reversible | Backfill | Slice |
|---|---|---|---|---|
| `0003_tasks` | Creates `tasks`, RLS enabled, policy scoped to `user_id`, grants to `authenticated` | yes | none, new table | 1 |
| `0004_pending_captures` | Creates `pending_captures`, RLS enabled, policy scoped to `user_id` | yes | none, new table | 1 |
| `0005_user_settings` | Creates `user_settings`, RLS enabled, policy scoped to `user_id` | yes | none, new table | 2 |
| `0006_capture_turns` | Creates `capture_turns`, RLS enabled, policy scoped to `user_id` | yes | none, new table | 4 |

Numbering continues from epic 000's `0001_ai_usage` and `0002_ai_user_limit`,
the only migrations that exist yet.

## 6. State management

| State | Lives in | Lifetime | Invalidated by |
|---|---|---|---|
| Capture input, palette selection | React component state, `CaptureStore` (MobX) | One composition, cleared on submit | Submit, Escape |
| Tasks, pending captures | `RecordsStore`, `CaptureStore` (MobX) | Session, refetched on mount | A mutation response in the same tab, per build plan §4 |
| Settings (timezone) | `SettingsStore` (MobX) | Session, refetched on mount | `updateTimezone` response |
| Offline-cached records | Service worker cache (Cache API) | Until the next successful online fetch | A successful `records` query while online |
| Theme (light/dark) | Not stored. `tokens.css` defines both modes behind `@media (prefers-color-scheme: dark)` | n/a | The OS setting changing. Pure CSS: the browser re-evaluates the media query and swaps custom properties on its own, no JS listener needed |

## 7. Error handling

Moved to the sub-plans. Each slice's failures are its own; the nine-member
union in build plan §7 is the one shape all of slice 1's failures share, and is
covered there, not repeated per sub-plan.

## 8. Test plan

Only cases spanning slices.

| id | Level | Case | Covers | Verified |
|---|---|---|---|---|
| T-X.1 | e2e | A task created in slice 1's flow appears in slice 2's Records view without a reload | FR-13, build plan §4 | 2026-09-14, live browser: captured a task, switched to Records by clicking the nav item (no F5), it was there. "Without a reload" reads as no hard refresh — `RecordsController` fetches `network-only` on every mount, so ordinary client-side navigation already satisfies it |
| T-X.2 | e2e | Editing a task's title in Records (slice 2) and reopening it shows the edit, origin still reads "command" | FR-19, FR-22 | 2026-09-14, live browser: edited a title, saved, navigated away and back (fresh fetch), edit persisted, origin still "Command" |
| T-X.3 | integration | User A's task, pending capture and settings are all invisible to user B | FR-6, T7, one case per table | Covered, as four separate tests rather than one: `test_capture_boundary.py::test_user_sees_only_their_own_tasks`, `::test_user_sees_only_their_own_pending_captures`, `test_identity_graphql.py::test_user_a_and_user_b_each_get_their_own_settings_row`, `test_capture_history_graphql.py::test_user_a_never_sees_user_bs_history` (capture_turns, added slice 4). `test_rls_boundary.py::test_every_user_table_is_locked_down` is the structural half, sweeping every table including new ones automatically |
| T-X.4 | e2e | With the network disabled, Records (slice 3's offline cache) still shows every task from the last online load | FR-40 | Verified in slice 3's own dev log entry (backend stopped outright, not just `navigator.onLine` toggled) |
| T-X.5 | e2e | The app opened with the OS in dark mode renders every slice 1 and slice 2 surface in dark tokens, no light-only element | proposed FR-42 baseline, product.md §10 | Verified in slice 3's own dev log entry (T-3.6) |

## 9. Rollout

| Item | Decision |
|---|---|
| Feature flag | None. This is the first user-facing feature; there is nothing to flag against |
| Rollout stages | Slice 1 deploys and is usable stand-alone (capture with no way to browse it). Slice 2 follows, then slice 3 |
| Kill switch | Inherited: `GATEWAY_ENABLED=false` already refuses every capture at the gateway. No second switch needed here |
| Metrics to watch | Captures per day, refusals by `CaptureResult` member, share of captures answered via a pending question, per PRD §8 |
| Rollback plan | All three migrations are reversible. The application rolls back by redeploying the previous image; no data migration to undo |

## 10. Task breakdown

Moved to the sub-plans. Slice order is section 2.

## 11. Definition of done

The feature is done when every sub-plan is done and:

- [x] All tasks shipped or explicitly dropped in the dev log, by id.
- [x] The five cross-slice cases in section 8 pass. Checked 2026-09-14; see the Verified column above.
- [x] All migrations applied, each table RLS-enabled with a policy. Four now, not three: `0006_capture_turns` (slice 4) added since this line was written.
- [x] Implementation matches the approved design, or a change record explains why not. `RecordEditForm`'s due-date gap (04.2's own deferral) closed 2026-09-14, D-43.
- [ ] **The metrics named in PRD §8 are instrumented. Five of seven true as of 2026-09-19, two blocked:**
  - Covered, no new work: captures per active user per week and captures by command name (`tasks.created_at`/`user_id`/`original_input`); captures refused for a cap or outage (`ai_usage.outcome`, epic 000's table).
  - **Closed 2026-09-19:** corrections within five minutes of creation. `deleteTask` no longer hard-deletes; it sets `tasks.deleted_at`, so a deletion is now derivable the same way an edit already was, from `updated_at`/`deleted_at` against `created_at`.
  - **Closed 2026-09-19:** sessions where the user typed without a command (FR-9), and weekly actives opening a records view. Both write to a new `events` table (`app/domains/analytics/`): `submit_capture.py` logs `no_command_input` on the guidance branch, and a new `recordsViewOpened` mutation, called once when the records view mounts, logs `records_view_opened`.
  - Still not covered, blocked outside this feature: week-four retention by signup cohort needs a signup date, which needs accounts — epic 002 (Authentication), not yet built.
- [ ] `index.md` updated to `shipped`. Left as `in-review`: cohort retention is still genuinely open, blocked on epic 002, not a formality.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-19 | Two of the three real PRD §8 metric gaps closed. New table `events` (`app/domains/analytics/`, migration `0014_events`), logging `no_command_input` (FR-9, from `submit_capture.py`) and `records_view_opened` (a new `recordsViewOpened` mutation, called on the records view's mount). `tasks` gains `deleted_at` (migration `0013_tasks_soft_delete`); `deleteTask` now soft-deletes, every read path filters `deleted_at IS NULL`, closing the deletion half of the "corrections within five minutes" metric. This is new scope on an approved, locked plan, added directly rather than through a full re-review, on explicit user instruction: `backend/tests` (unit + touched integration), mypy strict, and ruff all pass; `frontend` build, lint and tests pass; `frontend/schema.graphql` regenerated from the live backend schema. Cohort retention (blocked on epic 002) is the one metric gap still open | User: "use soft delete dont hard delete any data record, proceed with the implementation" | user |
| 2026-09-14 | §8's five cross-slice cases checked against reality and recorded, all pass (T-X.1/T-X.2 live in a browser, T-X.3 cross-referenced to four existing boundary tests plus the standing RLS sweep, T-X.4/T-X.5 cross-referenced to slice 3's dev log). §11's Definition of Done updated to match: migrations and cross-slice cases checked off; the metrics box audited honestly against PRD §8's seven named metrics — 3 already covered by existing tables (`tasks`, `ai_usage`), 1 partial (edits yes, deletes no audit trail), 3 not covered (2 buildable, 1 blocked on epic 002's accounts). Feature left `in-review`, not `shipped`, until the three real metric gaps are resolved one way or another | User asked to record the two open Definition-of-Done items | user |
| 2026-09-14 | Slice 4 marked approved | User approved `04.4` | user |
| 2026-09-14 | `Tables touched` section added at the top, per the new doc rule in `process-docs/CLAUDE.md` | User asked that any feature touching tables name them at the top of the doc | user |
| 2026-09-14 | Slice 4, `04.4-chat-history-and-loading-feedback.md`, added to §2's slice list, depending on 1 and 2. `0006_capture_turns` added to §5 | User asked for a history action on the Capture page and loading feedback on in-flight edits, added as a fourth slice per FR-44 to FR-46 | pending |
| 2026-09-13 | **Index approved.** §6's theme row corrected: no JS listener needed, a plain CSS media query does it | Slice 3's drafting caught the overstatement; user approved the index | user |
| 2026-09-13 | Created as the index, split into three slices | Build plan approved | pending |
