---
doc: dev-log
feature: 006-expenses
title: Expenses
stage: 5
status: draft
owner: claude
created: 2026-10-02
updated: 2026-10-02
approved_on: null
supersedes: null
---

# Dev Log — Expenses

Context: [Implementation plan](./04-implementation-plan.md) ·
[Sub-plan 4.1](./04.1-record-and-browse.md)

Appended as work happens. Nothing below is committed yet; all of it sits in the
working tree on `feat/006-expenses`.

## Done

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|
| T-1.1 | 4.1 | Migrations `0037` to `0039` | done | Upgrade, three downgrades and re-upgrade clean on local PostgreSQL. RLS enabled and forced, `expenses_own_rows` policy, `authenticated` grant checked |
| T-1.2 | 4.1 | Expenses domain: model, repository, service, interactors | done | C-14 to C-16 pass in unit and integration |
| T-1.3 | 4.1 | Expenses GraphQL with the `Paise` scalar | done | C-19 passes: ₹5 crore round-trips as `"5000000000"` |
| T-1.4 | 4.1 | `amount_reading.py` | done | C-1 to C-3 pass, 38 cases |
| T-1.5 | 4.1 | `ExpenseCaptureService.capture` and `next_step` | done | C-4, C-5, C-11 to C-13 pass |
| T-1.6 | 4.1 | Pending kinds, `resume`, chained questions | done | C-6 to C-10 pass; the chain also verified against the database |
| T-1.7 | 4.1 | Capture GraphQL union members, turns, events | done | `test_expense_capture_graphql.py`, 6 cases pass |
| T-1.8 | 4.1 | Records All tab gains expenses | done | C-20 passes, unit and integration |
| T-1.14 | 4.1 | Live evaluation runs | done | NFR-4 92.1% to 93.7%; NFR-5 100% in four of five runs after the user's correction. See below |
| T-1.13 | 4.1 | Design deltas in styles | done | `.dot.exp`, `.amt`, `.choicechip`, `.cal` as Tailwind classes; `--color-on-accent` in all three token blocks. Dark checked in T-1.15 |
| T-1.15 | 4.1 | Browser pass, light and dark | done, differences below | Worktree on ports 8006 and 4173 against `slashit_006_test`, signed in as the user's dev account |
| T-1.9 | 4.1 | Boundary and redaction tests | done | C-17 passes through GraphQL and under RLS alone; C-18 passes |
| T-1.10 | 4.1 | Frontend data layer | done | `schema.graphql` re-exported; `ExpenseFields`, four operation folders, three union members in both capture mutations, `ExpensesStore`, `money.ts`, `Paise` mapped to `string` in codegen. F-3 passes |
| T-1.11 | 4.1 | `DatePicker` and the capture cards | done | `ExpenseCards.tsx`, `src/components/DatePicker.tsx`, `utils/localDate.ts`; four new turn statuses in `CaptureStore`. F-1, F-2 pass, plus five controller cases |
| T-1.12 | 4.1 | Expenses tab, All rows, detail, edit, delete | done | `ExpensesController`, `ExpenseDetailController`, `ExpenseTable`, `ExpenseEditForm`, `ExpenseDetailView`, `ExpenseCategoryChips`, `EmptyExpenses`; routes; expense rows in All, related and search rows. F-4, F-5 pass |

Frontend on 2026-10-02, after T-1.10 to T-1.12: 328 tests in 62 files pass;
`tsc -b`, `vite build` and `oxlint` are clean (one existing warning in
`main.tsx`).

Backend suite state on 2026-10-02: every unit test passes; the three new integration
files pass against local PostgreSQL with the model faked. `ruff`, `ruff format`
and `mypy --strict` on `app/` are clean. The full integration suite, re-run after
the changes (expense live evaluation excluded, run separately in T-1.14), has
seven failures, none in code this feature touches. Two are the baseline's live
evaluations (004 category accuracy, 005 search quality). Five are in
`test_firing_and_notifications.py`, all `procrastinate.exceptions.AppNotOpen`
from `email_queue.enqueue_email`. The baseline had one of them; the same file
on a clean `main` checkout fails six, so the count moves with the environment,
not with this branch. Owner: 003's test harness, not 006.

## In progress

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|

Live runs against the real model, 2026-10-02:

| Set | Target | Run 1, instruction as in the index | Run 2, D-4 instruction | Run 3, every number |
|---|---|---|---|---|
| Categories, 63 cases (NFR-4) | over 85% | 82.5% | **92.1%** | 92.1% |
| Amounts, 50 cases (NFR-5) | over 98% | 84.0% | **94.0%** | 92.0% |

The code holds the run 2 instruction. Its three amount misses are the cases
`expense_amounts.json` itself calls debatable:

| Input | Expected | Got |
|---|---|---|
| `bowling with 6 people 2400` | save | asks which of ₹6 and ₹2,400 |
| `room 101 hotel 4500` | asks which number | saves ₹4,500 |
| `iphone 15 case 999` | asks which number | saves ₹999 |

The set expected `2 coffees 180` and `dinner for 4 at 3200` to ask, but
`bowling with 6 people 2400` to save, so no single instruction scored all
three. "Over 98%" on 50 cases means all 50 must pass.

User decision, 2026-10-02: a count of people or items asks which number is the
amount; a number inside a name is never one. The three cases now expect ask,
save and save, and the file is marked approved. No code changed.

Runs after the correction, same run 2 instruction:

| Run | NFR-5, 50 cases | NFR-4, 63 cases |
|---|---|---|
| 4 | 98.0%, one miss, fails "over 98%" | — |
| 5 | 100% | — |
| 6 | 100% | — |
| 7 | 100% | 93.7% |
| 8 | 100% | 92.1% |

Run 4's miss was not printed. The model is not deterministic at this margin:
one wrong case in 50 fails the target. NFR-4's misses repeat across runs:
`Rapido to the airport` read as travel, `Health insurance premium` and
`Spotify premium` as bills, a wedding gift and a visa fee as other.

## Yet to be done

| # | Sub-plan | Task | Blocked on |
|---|---|---|---|
| — | 4.1 | NFR-2 at p95 over a real sample | Six live model calls in T-1.15 took 1.6 s to 3.3 s; not enough for a p95 |
| — | 4.1 | Update `index.md`'s 006 row | End of slice 1 |
| — | 4.2 | Draft sub-plan 4.2, summaries, then build it | Slice 1 |
| — | 4.3 | Draft sub-plan 4.3, search, then build it | Slice 1 |

## Browser pass, 2026-10-02

Compared in a running app, dark then light: `Main`, `ExpenseAsk`, `AmountPick`,
`DatePick`, `CaptureStates` (another currency), `CaptureMoreStates`
(loading), `RecordsAll`, `RecordsExpenses`, `ExpensesStates` (filtered),
`ExpenseDetail`, `ExpenseEdit`, `DetailStates` (amount not valid),
`DeleteExpense`, and the four dark artboards. Not driven live: the over-long
and model-down refusals, offline, signed out and not found; each has a
component test.

| Artboard | Difference | Action |
|---|---|---|
| `DetailStates` | Error text sat on the Category label; field had no red ring | Fixed in `ExpenseEditForm.tsx` |
| `Main` | The model's description keeps the user's case: "dinner with friends", drawn "Dinner with friends" | Open. FR-11 stores the user's own words |
| `AmountPick` | `dinner for 4 at 3200` saved as "dinner for": the model strips both candidate numbers from the description. An instruction keeping counts dropped NFR-5 to 90%, so it was reverted | Deferred, see below |
| `AmountPick` | `2 coffees 180` saved ₹180 without asking in one live run; the set expects the question | Model variance, as in T-1.14 |
| `ExpenseAsk` | After a rejected answer the amount field loses focus | Open, minor |
| All capture cards | A tall saved card lands partly under the dock; the stream scrolls when a turn is added, not when it grows | Existing 001 behaviour |
| `ExpenseAsk`, `ExpenseEdit` | Primary buttons and the selected segment use white text on blue in dark; the design uses `#1c1917` | Existing `Button` and segment styles, app-wide |
| `RecordsExpenses` | No band, period picker or search box | Slices 2 and 3; D-12 |

## Deviations from the plan

None of these is approved yet.

| # | Date | Planned | Actual | Why |
|---|---|---|---|---|
| D-1 | 2026-10-02 | Index §4 schema: five required fields, `currency` and `local_date` typed `["string", "null"]` | `date_words` added; `currency`, `local_date` and `date_words` optional plain strings | Design §8's date question names the user's phrase ("Next Saturday reads as…"), which the planned schema never returned. Optional strings are the shape every other capture schema uses with this provider; nullable type arrays are unproven with it. The phrase waits in `pending_captures.known_title`, so no migration changed |
| D-2 | 2026-10-02 | `ExpenseService` publishes get, update and delete | Those three are Records-side interactors only; the service publishes create and list | No other domain calls them. Publishing them would duplicate the interactors' rules |
| D-3 | 2026-10-02 | Answering a question is one transaction: delete pending, insert expense, record turn | Three writes, as every other capture answer does. A chained question does replace its row in one transaction | The insert belongs to expenses and the rest to capture; one transaction across them needs a shared unit of work no domain has yet |
| D-4 | 2026-10-02 | Index §4 instruction: skip "dates, times and quantities" | Counts are listed; a category guide is added; a day with no month reads as the most recent such day | Skipping quantities contradicts FR-5's own example and the approved evaluation set. Raised NFR-4 from 82.5% to 92.1% and NFR-5 from 84% to 94% |
| D-5 | 2026-10-02 | `LocalDatePort` in expenses for edit validation | Not built | FR-21 accepts any date on edit, so nothing reads it. Slice 2's period parser may add it |
| D-6 | 2026-10-02 | `ExpenseQuestionAsked { pendingId … }` | `pendingCaptureId` | Matches every other capture question type the frontend already reads |
| D-7 | 2026-10-02 | — | `ExpenseRefused` and `ExpenseInvalid` carry a `message`; `ExpenseInvalid` adds `length` for an over-long description | Every other refusal type carries its copy; the edit form shows the count |
| D-8 | 2026-10-02 | `expense_amount_asked` event, unqualified | Carries `{"is_choice": bool}` | Tells FR-5's question from FR-3's for the build plan's risk triggers. Numbers and booleans only, per migration 0036's check |
| D-9 | 2026-10-02 | `ExpenseCategoryTag.tsx` in `features/records/components/` | In `src/components/`, beside 004's `CategoryTag` | Capture's saved card uses it too; the repo rules put cross-feature components there |
| D-10 | 2026-10-02 | `DeleteExpenseModal.tsx` | Not built; 003's `DeleteConfirmModal` takes the title, message and labels | It already draws `DeleteExpense`'s dialog, busy and failed states |
| D-11 | 2026-10-02 | `GetRecords` selects `...ExpenseFields` | Selects the fields inline, aliasing `category` and `originalInput`; the response handler renames them back. `ExpenseRefused`'s `reason` and `length` are aliased in both capture mutations | GraphQL rejects one response key with two types: Memory's `category` and nullable `originalInput`, MalformedResult's `reason`, MemoryTooLong's non-null `length` |
| D-12 | 2026-10-02 | `RecordsExpenses` draws a search box | No search box on the Expenses tab in slice 1; text left from another tab does not apply there | Search over expenses is slice 3 (FR-29); the search query has no expense type yet |
| D-13 | 2026-10-02 | `AmountPick` draws the chosen amount as a new turn above the saved card | The answer replaces the question card in place, as every 001 to 004 question does | One answer flow for every command. Logged for T-1.15's comparison |
| D-14 | 2026-10-02 | — | Records shows the amount-choice card with chips only, no typed field | `AmountPick` draws none. The server still accepts a typed amount |
| D-15 | 2026-10-02 | — | The Expenses tab shows the offline note over loaded rows, as the Reminders tab does | `ExpensesStates` draws it; the plan's file list did not name it |

## Deferred

| Item | Why deferred | Where it goes next |
|---|---|---|
| A description loses a count the model read as a candidate amount (`dinner for 4 at 3200` saves "dinner for") | User, 2026-10-02: leave it; Edit corrects it. Tuning the instruction cost NFR-5 | Revisit when slice 3 changes the extraction instruction |
| Unexpected errors reach the client unmasked and their tracebacks reach the log unredacted | User, 2026-10-02: app-wide, so its own platform change after slice 1, not 006 | A platform follow-up, to be named in `index.md` |

## Incidents and defects

| Date | What broke | Cause | Fix |
|---|---|---|---|
| 2026-10-02 | Browser pass: the first save failed with a foreign-key error on `expenses.user_id` | The worktree's `slashit_006_test` database has no `auth.users` row for the signed-in account; tasks have the same key | Added the account's id to that test database's `auth.users`. Not a code defect |
| 2026-10-02 | The foreign-key error reached the screen as raw SQL, with the typed text in its parameters, and the same text went to the server log | The GraphQL schema masks no unexpected errors, and exception tracebacks bypass `USER_TEXT_KEYS` redaction. Both are app-wide | Deferred to a platform change, see below. NFR-7 is not met for unexpected errors until then |
| 2026-10-02 | Port 4173 served a stale build | A service worker from an earlier `vite preview` on that port | Unregistered in the test browser |
| 2026-10-02 | A generated `search_vector` on `category::text` would not create | An enum's text output is STABLE, not IMMUTABLE | The migration spells the category out with a `CASE` |

## Notes for the next feature

- One selection set cannot hold the same field name with two types across
  union members. A new record type in a mixed union (`RecordItem`,
  `SearchRecord`) will need the aliasing in D-11.

- `strawberry.scalar` on a class is deprecated and fails `mypy`; a custom
  scalar is a `NewType` mapped through `StrawberryConfig.scalar_map` in
  `graphql/schema.py`.
