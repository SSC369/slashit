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
| T-2.1 | 4.2 | `periods.py` | done | C-22 to C-26 pass, 22 cases |
| T-2.2 | 4.2 | `LocalDatePort` adapter, grouped sum, `summarise`, `periods` | done | Unit C-27, C-28. `Period` and `PeriodKey` live in `interfaces/dtos.py` so the GraphQL types do not import `services/`. Closes D-5 |
| T-2.3 | 4.2 | `expensePeriods`, `expenseSummary` | done | Integration C-27, C-28 against PostgreSQL |
| T-2.4 | 4.2 | `/expenses` in capture | done | C-29, C-32. `ExpensePort` gains `summarise_text`; no new interactor collaborator |
| T-2.5 | 4.2 | Boundary and load tests | done | C-30 passes. C-31, local PostgreSQL, 5,000 expenses, This year, 50 calls each: `expenseSummary` p50 11 ms, p95 13 ms; `expenses` p50 77 ms, p95 86 ms. NFR-3 under 1 s |
| T-2.6 | 4.2 | Frontend data layer and store | done | No codegen clash; `ExpenseSummary` needed no aliases |
| T-2.7 | 4.2 | Summary card, empty form, refusal note, loading, history row | done | F-6, F-7 |
| T-2.8 | 4.2 | Period picker, band, Expenses tab states, Open in Records | done | F-8 to F-10. The band shows only totals whose range matches the picked period |
| T-2.9 | 4.2 | Design deltas | done | `--color-bar-track` in all three token blocks; dark checked in T-2.10 |
| T-2.10 | 4.2 | Browser pass | done, differences below | `ExpenseDiscovery`, `DarkSummary`, `SummaryStates` (empty, not understood), `DarkRecordsExpenses`, `RecordsExpenses`, `ExpensesStates` (empty period). `/expenses` and the band both read ₹3,680 for October |
| T-1.10 | 4.1 | Frontend data layer | done | `schema.graphql` re-exported; `ExpenseFields`, four operation folders, three union members in both capture mutations, `ExpensesStore`, `money.ts`, `Paise` mapped to `string` in codegen. F-3 passes |
| T-1.11 | 4.1 | `DatePicker` and the capture cards | done | `ExpenseCards.tsx`, `src/components/DatePicker.tsx`, `utils/localDate.ts`; four new turn statuses in `CaptureStore`. F-1, F-2 pass, plus five controller cases |
| T-1.12 | 4.1 | Expenses tab, All rows, detail, edit, delete | done | `ExpensesController`, `ExpenseDetailController`, `ExpenseTable`, `ExpenseEditForm`, `ExpenseDetailView`, `ExpenseCategoryChips`, `EmptyExpenses`; routes; expense rows in All, related and search rows. F-4, F-5 pass |

Frontend on 2026-10-02, after slice 2: 344 tests in 65 files pass. After
slice 1 it was 328 tests in 62 files;
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
| E-1 | 4.1 | Malformed id reads as `ExpenseNotFound` | done, 2026-10-03 | `parse_expense_id` in `expenses/graphql/errors.py`, used by `expense`, `updateExpense`, `deleteExpense`. The same `UUID(str(id_))` pattern in memories, reminders, records and search is not changed here: see Notes |
| E-2 | 4.1 | Amounts past the storage ceiling refused | done, 2026-10-03 | `MAX_AMOUNT_PAISE` (bigint). Line: `ExpenseRefused(AMOUNT_TOO_LARGE)`; answer: the question again with the too-large copy; edit: `ExpenseInvalid(TOO_LARGE)`. PRD FR-2 change record. Decision 1A |
| E-3 | 4.1 | Long `/add-expense` line gets FR-13's refusal | done, 2026-10-03 | `/add-expense` joins memory and search under the 1,000 outer guard |
| E-4 | 4.1 | Edit form counts characters, not UTF-16 units | done, 2026-10-03 | `[...text].length`; test with 150 emoji |
| E-5 | 4.1 | Chip answers carry a marker | done, 2026-10-03 | Decision 2A. See D-21 |
| — | 4.1 | Expense marker is a ₹ glyph | done, 2026-10-03 | Decision 3A. See D-22 and the design change record |
| — | 4.1 | NFR-5 amount set grows to 100 cases | done, 2026-10-03 | Decision 5A. Cases 51 to 100 approved by the user the same day. Live run owed: needs a provider key |
| E-6 | 4.1, 4.2 | Edge-case pass in a browser | done, 2026-10-03 | Dark theme. Four defects found and fixed; see "Edge-case browser pass, 2026-10-03". Decision 4A's two items fixed |
| T-3.1 | 4.3 | `amount_from_search` | done, 2026-10-03 | C-33: 25 cases, the same table as capture's `normalise_amount` |
| T-3.2 | 4.3 | Repository search, embedding methods | done, 2026-10-03 | C-34 to C-36 against PostgreSQL. An exact amount is OR-ed into the shared word-or-meaning match, counts as every term present, and sorts first (Q2) |
| T-3.3 | 4.3 | Embed adapter, queue, interactors, jobs | done, 2026-10-03 | C-37, C-38. `expenses.embed_expense` (three attempts), `expenses.backfill_embeddings` every ten minutes; registered in `core/jobs.py`. A save and a description edit queue the embed |
| T-3.4 | 4.3 | `SearchPort.text`, `ExpenseSearchAdapter`, `RecordType.EXPENSE`, wiring | done, 2026-10-03 | C-12 now covers five types; C-39 `/search 850` end to end |
| T-3.5 | 4.3 | `describe_record` for expenses | done, 2026-10-03 | "expense, ₹850.50 on Fri 02 Oct 2026, transport" |
| T-3.6 | 4.3 | Frontend operations, codegen, search card group | done, 2026-10-03 | F-11. `ExpenseRecordFields` fragment carries D-11's aliases for records, search and related; one `toRecordItem` in `api/lib/recordItem.ts` undoes them. The capture card selects display fields only, which do not clash |
| T-3.7 | 4.3 | Expenses tab search; related records on detail | done, 2026-10-03 | F-12, F-13. Opening the tab from a summary card clears search text left from another tab |
| T-3.8 | 4.3 | Browser pass, dark and light | done, 2026-10-03 | See "Browser pass, slice 3". No differences from `SearchExpense` beyond the word-only strip, which shows because no model key was reachable |
| T-3.9 | 4.3 | Deploy note | done, 2026-10-03 | At deploy, defer `expenses.backfill_embeddings` once with `full=True`, as 005 did for its types. Added to epic 012's list in `index.md` |

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
| — | 4.1 | NFR-2 at p95 over a real sample | A provider key. Six live model calls in T-1.15 took 1.6 s to 3.3 s; not enough for a p95 |
| — | 4.1 | NFR-5 live run over the 100-case set | A provider key |
| — | 4.3 | Meaning search and the embed job against the real model | A provider key. Covered here by the fake embedder and stored vectors |

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

## Edge-case pass, 2026-10-02, in progress

Asked by the user: test every UI and functional edge case. Stopped part way
when the session ended; the rest is E-6.

`backend/tests/integration/test_expense_edge_cases.py` is new and runs against
local PostgreSQL with only the model faked. Ten of its sixteen cases pass; the
six failures are E-1 (four ids), E-2 and E-3 above. They are left failing on
purpose until fixed. All sixteen pass from 2026-10-03, after the E-1 to E-3 fixes.

| Passes | Case |
|---|---|
| ✓ | ₹10,00,00,00,00,00,000, 10^16 paise and past 2^53, saves and sums exactly through GraphQL |
| ✓ | `<script>`, `&` and emoji in a description come back as typed |
| ✓ | 200 emoji fit a description; 201 are `TOO_LONG` with length 201; whitespace only is `EMPTY` |
| ✓ | An edit to 0 or −500 paise is `ExpenseInvalid`, `NOT_POSITIVE` |
| ✓ | Period edges are inclusive; the day before and after last month do not count; the last day of this month, still ahead, does |
| ✓ | `/expenses   LAST   Month  ` reads; `/EXPENSES` is an unknown command, as every command name is matched exactly |
| ✓ | A deleted expense cannot be edited, deleted again, listed or counted |

## Browser pass, slice 2, 2026-10-02

| Artboard | Difference | Action |
|---|---|---|
| `RecordsExpenses` | The period menu's 19 options run past its 360 px height | The menu uses the `scroll` class, which exists on `main` (`4d0b14a`) but not on this branch. Fixed by merging `main` |
| `RecordsExpenses` | The band's label "Spent · October 2026 so far" wraps to two lines in its 210 px cell | Open, minor |
| `ExpensesStates` | A new user on this month sees "No expenses recorded this month", not "No expenses yet"; the example command shows on All time | The tab knows only the picked period's count. Open, minor |
| `SummaryStates` | The summary card's history row reruns the line, as a search's does | No artboard draws it; follows 005 |

## Browser pass, slice 3, 2026-10-03

Same setup as the edge-case pass, dark and light. Two expenses were given the
same stored vector so related records had something to show; the query's own
meaning was unavailable, as no model key was reachable.

| Artboard or flow | Result |
|---|---|
| `SearchExpense`: `/search 850` | "3 records match "850"": an Expenses group of two ₹850 spends with the ₹ marker, day and amount, then the ₹850 task; footer "A number also matches expenses of exactly that amount". Matches, apart from the amber word-only strip |
| Records, Expenses tab, search "dinner" | Two expenses, best match first; the period picker and band hidden while searching (Q3) |
| Expense detail | Related lists the other expense with the same vector, with ₹ marker, day and amount |

## Edge-case browser pass, 2026-10-03

Run in Chromium against the app on a local PostgreSQL 16 with pgvector,
dark theme, 1440 × 900. Signed in with a locally signed token the backend
trusted through a local JWKS, and Supabase's auth calls intercepted, as 002
did for slice 2; no Supabase project or model key was reachable. Expenses
were seeded into the database: one per category, a 200-character
description, an amount at the storage ceiling, and a deleted one.

| Case | Result | Action |
|---|---|---|
| All tab: ₹ marker, ceiling amount, 200-character description, deleted expense hidden | As designed | — |
| Band at the ceiling: total and Shopping cell clipped past their cells | Defect | Fixed: band amounts wrap (`bandMoneyStyles`) |
| Band label "Spent · October 2026 so far" on two lines | Defect, decision 4A | Fixed: the cell grows from 210 px to at most 320 px, label on one line |
| All eight categories in the band | As designed | — |
| Period menu: 19 options scroll; Escape closes it | As designed | — |
| Detail at the ceiling amount | As designed | — |
| Detail with a 200-character description: the breadcrumb ran to three lines | Defect | Fixed: the breadcrumb truncates at 420 px, full text in its title |
| `/records/expenses/abc` and a deleted expense's URL | "This expense no longer exists" | E-1 holds end to end |
| Delete, then Back | The not-found card, with the toast | As designed |
| Edit: `.5` | Refused, "Enter an amount above ₹0…" | As capture reads it: a leading digit is required |
| Edit: `1,2,3` | Read as ₹123 | FR-2 accepts commas in any grouping |
| Edit: empty | Save disabled | — |
| Edit: 20 nines | "That amount is too large to save. Check it for an extra zero." from the server, cleared when corrected | E-2 holds end to end |
| Calendar from October 2026 to January 2027 | Fri 1 Jan 2027 picked | — |
| Two bare `/add-expense` lines | Two amount questions open side by side | — |
| Reload with both open | Both leave the stream; History keeps them as "Question asked" | 001's design for every command: the stream is per session |
| A user with other records and no expenses, on this month | "No expenses recorded this month" | Defect, decision 4A. Fixed: an empty period asks once for the all-time count; none gives "No expenses yet" with the example command |

Not driven: anything that needs the model (a two-number line's chips, the
too-large and long-description refusals from a typed line). Each has unit
and integration tests. Light theme not checked in this pass.

## Decisions, 2026-10-03

Asked as multiple choice; the user took every recommendation ("go with your
recommendation").

| # | Question | Decision |
|---|---|---|
| 1 | E-2: amounts past the storage ceiling | A. Refuse with "That amount is too large to save"; FR-2 amended |
| 2 | E-5: typed digits equal to a chip's paise | A. Chips send a marker; typed digits are always rupees |
| 3 | Expense marker looks like 007's event diamond | A. A ₹ glyph; design change record |
| 4 | Band label wrap, new-user empty-state copy | A. Fix both inside E-6 |
| 5 | NFR-5 flaky at 50 cases | A. Grow the set to 100, keep "over 98%" |
| 6 | Order of work | A. E-1 to E-4, then E-6, then draft 4.3 |

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
| D-16 | 2026-10-02 | 4.2 §4: `PeriodNotUnderstood` mapped in capture | Expenses returns `PeriodNotUnderstood`; capture turns it into `ExpenseRefusedDTO(PERIOD_NOT_UNDERSTOOD, period_text)` | As planned; recorded because `ExpenseRefusedDTO` gained `period_text` for FR-27's quote |
| D-17 | 2026-10-02 | 4.2 §4 lists no `pyproject.toml` change | A `slow` pytest marker for C-31 | `--strict-markers` rejects an unregistered marker |
| D-18 | 2026-10-03 | Index: migrations `0037_expenses`, `0038_capture_expense`, `0039_expense_events`, after `0036_event_properties` | `0039_expenses`, `0040_capture_expense`, `0041_expense_events`, after 007's `0038_capture_events` | 007 reached `main` first with `0037` and `0038`. Every change on both sides only adds enum values and columns, so the chain is re-pointed with no content change. One head, checked with `alembic heads`. Change records on the build plan, the index and 4.1 |
| D-19 | 2026-10-03 | Index §1: all three slices reach `main` together, since 005's FR-11 wants a new record type searchable | Slices 1 and 2 merged into `main` from `feat/006-expenses`, before sub-plan 4.3 exists. Expenses are not searchable on `main` until slice 3 lands | User, 2026-10-03: "pull feat/006-expenses into main", after being told it left §1. 006 stays unshipped until slice 3; 005's FR-11 is unmet for expenses until then |
| D-20 | 2026-10-03 | 4.1 file map: `features/records/utils/recordPath.ts` | Folded into 007's `src/utils/recordPath.ts`, which gains `EXPENSE` and `recordId`, with its `never` check on both | Both epics added a `recordPath` in different places; one module keeps frontend rule 3's exhaustiveness check. Merge-only changes besides: the Records search box is hidden on both the Events and Expenses tabs, and tests that build the capture and records interactors pass both epics' ports |
| D-21 | 2026-10-03 | 4.1 §5: a chip sends the candidate's paise | A chip sends `chip:<paise>`, accepted only for a listed candidate; bare digits are rupees. The turn logs the chip as the amount it showed (`₹180`), not the marker; before this, history showed a chip answer as raw paise, "Answered: 18000" | Decision 2A (E-5). `format_rupees` added to `amount_reading.py` for the log |
| D-22 | 2026-10-03 | Design §6 `.dot.exp`, a green diamond, drawn as a styled `span` | `src/components/ExpenseMarker.tsx`, lucide's `IndianRupee` at 12 px in `text-success`, beside 007's `EventMarker`; `typeDotExpenseStyles` removed | Decision 3A. Design change record |
| D-23 | 2026-10-03 | 4.2: the Expenses tab loads periods, list and summary | An empty period also asks for the all-time summary once, into `ExpensesStore.hasAnyExpense`, to tell a new user's tab from an empty month | Decision 4A. No schema change: it reuses `expenseSummary` with no range |

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
| 2026-10-03 | CI red on `main` for `c5f9f5e` and `6843d16`: ruff E501 in `test_expense_capture_graphql.py` | The E-5 change made one line 90 characters; `ruff check` was run before that last edit, not after | Rewrapped; shipped with slice 3. Lint now runs last, after every edit |
| 2026-10-02 | Port 4173 served a stale build | A service worker from an earlier `vite preview` on that port | Unregistered in the test browser |
| 2026-10-02 | A generated `search_vector` on `category::text` would not create | An enum's text output is STABLE, not IMMUTABLE | The migration spells the category out with a `CASE` |

## Notes for the next feature

- One selection set cannot hold the same field name with two types across
  union members. A new record type in a mixed union (`RecordItem`,
  `SearchRecord`) will need the aliasing in D-11.

- `strawberry.scalar` on a class is deprecated and fails `mypy`; a custom
  scalar is a `NewType` mapped through `StrawberryConfig.scalar_map` in
  `graphql/schema.py`.

- The `UUID(str(id_))` pattern E-1 fixed in expenses also sits in memories,
  reminders, records and search: a malformed id there is still a raw error.
  App-wide, so it is a platform follow-up beside the unmasked-errors item in
  Deferred, not 006's to change.

- A fresh database cannot run `alembic upgrade head` in one go: an earlier
  migration adds `memory_forgotten` to an enum and uses it in the same
  transaction. Upgrading one revision at a time works. Found 2026-10-03 while
  standing up a local database; existing databases are unaffected.
