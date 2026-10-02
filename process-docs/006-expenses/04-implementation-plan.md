---
doc: implementation-plan
feature: 006-expenses
title: Expenses
stage: 4
status: approved
owner: user
created: 2026-10-02
updated: 2026-10-02
approved_on: 2026-10-02
supersedes: null
split: true
---

# Implementation Plan (LLD) — Expenses

> **Approved** by @user on 2026-10-02. Locked — changes require a change record (§7).

Context: [PRD](./01-prd.md) · [Design](./02-design.md) · [Build plan](./03-build-plan.md)

No code is written before this index and a slice's own sub-plan are approved.
The branch is cut from `main` after 005's open fixes land there (build plan §9).

Tables this feature touches, by migration:

| Table | New or changed | Migration | Slice |
|---|---|---|---|
| `expenses` | new: columns, `expense_category` enum, both checks, list index, GIN on `search_vector`, `embedding vector(768)`, forced RLS, policy, grant | `0037_expenses` | 1 |
| `pending_captures` | changed: four `missing_field` values, `expense_amount_paise`, `expense_description`, `expense_category`, `expense_spent_on`, `amount_candidates` | `0038_capture_expense` | 1 |
| `capture_turns` | changed: `resulting_expense_id`, outcomes `expense_saved`, `expenses_summarised` | `0038_capture_expense` | 1 |
| `events` | changed: seven expense event types | `0039_expense_events` | 1 |

All schema lands in slice 1, so slices 2 and 3 migrate nothing. The search
columns ship empty until slice 3's job fills them, which costs nothing and
keeps the table's shape fixed from the first row.

## 1. Scope recap

Everything in the approved PRD ships, in three slices. Slice 1 records an
expense with every question, refusal and the calendar, and browses, edits and
deletes it in Records. Slice 2 adds totals: `/expenses <period>`, the period
picker and the summary band. Slice 3 makes expenses searchable by words, meaning
and exact amount.

All three slices reach `main` together. 005's FR-11 requires a new record type
to be searchable from the day it ships, and an expense tracker without totals
fails G2. Each slice is still verifiable end to end on its own.

## 2. Split decision

| Trigger | Threshold | This feature |
|---|---|---|
| Tasks in the breakdown | more than 15 | about 35, `estimate` |
| Files created or modified | more than 25 | about 80, `estimate` |
| Independently shippable slices | more than one | three |
| Distinct boundaries touched | more than two | five: expenses, capture, records, search, analytics, plus the worker |
| Length of the drafted plan | more than 500 lines | over, as one document |

**Decision:** split into three sub-plans. Sub-plans 2 and 3 are drafted as the
slice before each lands, as 004 and 005 did.

### Slices

| # | Sub-plan | What works when it lands | Depends on | Status |
|---|---|---|---|---|
| 1 | [04.1-record-and-browse.md](./04.1-record-and-browse.md) | `/add-expense` saves with amount, description, category and date; the four questions, the calendar and the refusals work; Expenses tab, All tab, detail, edit and delete work, with every drawn state | none | approved 2026-10-02; building |
| 2 | `04.2-summaries.md` | `/expenses` with and without a period; the summary card and its states; period picker, category filter and band on the Expenses tab; totals match | 1 | not drafted |
| 3 | `04.3-search.md` | Embed job fills vectors; `/search` and Records search find expenses by words, meaning and exact amount | 1 | not drafted |

Slices 2 and 3 are independent of each other and may be built in either order.

## 3. Shared file map

Only the files more than one slice changes. Each sub-plan lists its own.

| Path | Slice 1 | Slice 2 | Slice 3 |
|---|---|---|---|
| `backend/app/domains/expenses/public.py` | created | adds summary and period types | adds search methods |
| `backend/app/domains/expenses/services/expense_service.py` | created | adds `summarise` | adds candidates and embedding lookup |
| `backend/app/domains/expenses/repositories/expense_repository.py` | created | adds the grouped sum | adds the search query |
| `backend/app/domains/capture/interactors/submit_capture.py` | `/add-expense` | `/expenses` | — |
| `backend/app/domains/capture/graphql/types.py` | expense union members | `ExpenseSummary` | — |
| `backend/app/domains/capture/constants.py` | `/add-expense`, extraction schema | `/expenses` | — |
| `backend/app/core/deps.py` | expenses wiring | summary wiring | search adapter, embed queue |
| `frontend/src/features/capture/components/ExpenseCards.tsx` | saved, refusals, questions | summary card | — |
| `frontend/src/stores/ExpensesStore.ts` | created | summary state, period | — |
| `frontend/src/features/records/controllers/ExpensesController/` | created | period, band | — |
| `frontend/src/constants/captureCommands.ts` | `/add-expense` | `/expenses` | — |

## 4. Interfaces and contracts

Only what crosses a slice or domain boundary. Python signatures are
keyword-only, per `backend/.claude/rules/code-rules.md`.

### Expenses published service, slice 1

```python
# expenses/public.py
class ExpenseCategory(StrEnum):
    FOOD, TRANSPORT, SHOPPING, BILLS, HEALTH, ENTERTAINMENT, TRAVEL, OTHER

@dataclass(frozen=True)
class ExpenseFields:
    amount_paise: int          # > 0, no upper bound (FR-2)
    description: str           # 1 to 200 characters, as typed (FR-11, FR-13)
    category: ExpenseCategory
    spent_on: date             # local calendar date (AD-3)

@dataclass(frozen=True)
class ExpenseDTO:
    id: UUID; user_id: UUID; amount_paise: int; description: str
    category: ExpenseCategory; spent_on: date; origin: Literal["command"]
    original_input: str; created_at: datetime; updated_at: datetime

@dataclass(frozen=True)
class ExpenseChanges:          # every field optional; None means unchanged
    amount_paise: int | None; description: str | None
    category: ExpenseCategory | None; spent_on: date | None

ExpenseService.create_expense(*, user_id, fields: ExpenseFields, original_input: str) -> ExpenseDTO
ExpenseService.list_expenses(*, user_id, category: ExpenseCategory | None,
                             start: date | None, end: date | None) -> list[ExpenseDTO]
ExpenseService.get_expense(*, user_id, expense_id) -> ExpenseDTO | ExpenseNotFound
ExpenseService.update_expense(*, user_id, expense_id, changes: ExpenseChanges)
    -> ExpenseDTO | ExpenseNotFound | ExpenseInvalid
ExpenseService.delete_expense(*, user_id, expense_id) -> ExpenseDeleted | ExpenseNotFound
```

`list_expenses` takes `start` and `end` from slice 1, unused by its callers
until slice 2, so the signature never changes. Slice 2 adds
`parse_period(*, text: str, today: date) -> Period | None` and
`summarise(*, user_id, period: Period, category: ExpenseCategory | None) -> ExpenseSummaryDTO`.
Slice 3 adds `search_candidates` and `embedding_of`, per 005's `SearchPort`.

### Amount reading, slice 1, used by capture only

```python
# capture/services/amount_reading.py, pure functions
def normalise_amount(*, raw: str) -> int | None        # "₹1,20,000" -> 12_000_000 paise; "1.2k" -> 120_000; "3 lakh", "5 crore"
def numbers_in(*, text: str) -> set[int]                # every amount-shaped number in the text, in paise
def keep_candidates(*, model_amounts: list[str], text: str) -> list[int]  # distinct, order kept
def names_foreign_currency(*, text: str) -> bool        # $, €, £, USD, EUR, GBP, AED, SGD, dollar, euro, ...
```

### The extraction call, slice 1

```python
EXPENSE_EXTRACTION_SCHEMA = {
  "type": "object",
  "properties": {
    "amounts": {"type": "array", "items": {"type": "string"}},
    "currency": {"type": ["string", "null"]},
    "description": {"type": "string"},
    "category": {"type": "string", "enum": ["food","transport","shopping","bills",
                 "health","entertainment","travel","other"]},
    "local_date": {"type": ["string", "null"]},   # ISO date, null means today
  },
  "required": ["amounts", "currency", "description", "category", "local_date"],
}
```

The instruction gives the user's local today, its weekday and the zone, from
`LocalClockPort`. It says to list every number that could be the price, to skip
dates, times and quantities where the text makes them clear, and to keep the
description in the user's words without the amount or date.

### GraphQL, for the frontend

Money crosses GraphQL as a custom scalar `Paise`, serialised as a decimal
string. GraphQL's `Int` is 32-bit and would cap an amount near ₹2.1 crore,
against FR-2's no-limit rule.

| Type or field | Slice |
|---|---|
| `scalar Paise`, `ExpenseCategory` enum | 1 |
| `Expense { id amountPaise description category spentOn origin originalInput createdAt updatedAt }` | 1 |
| `ExpenseSaved { expense }`, `ExpenseQuestionAsked { pendingId kind question amountCandidates readDate }`, `ExpenseRefused { reason length }` | 1 |
| `ExpenseQuestionKind`: `AMOUNT`, `DESCRIPTION`, `AMOUNT_CHOICE`, `DATE`. `ExpenseRefusalReason`: `FOREIGN_CURRENCY`, `DESCRIPTION_TOO_LONG` | 1 |
| `expenses(filter)`, `expense(id)`, `updateExpense`, `deleteExpense`, `ExpenseNotFound`, `ExpenseInvalid { field reason }` | 1 |
| `ExpenseSummary { label start end totals { category totalPaise } grandTotalPaise count }`, `expenseSummary(range, category)`, refusal reason `PERIOD_NOT_UNDERSTOOD` | 2 |
| `search` union gains `Expense` | 3 |

`ExpenseRefused` with `PERIOD_NOT_UNDERSTOOD` is added in slice 2, so the enum
grows by one value then; no client switch breaks on it, since slice 2 ships
its card in the same change.

## 5. Rollout and flags

No flag. The three slices are built and verified one at a time on the feature
branch and merge to `main` together, for §1's reasons.

Migrations run forward only in production. Each has a working `downgrade` for
development.

## 6. Evaluation sets, before this plan is approved

Build plan Q6: both sets are built before approval. Drafted with this plan, for
the user to correct.

| Set | Size | File | Pass bar |
|---|---|---|---|
| Categories: description and expected category, including ambiguous spends | 63 | `backend/tests/eval/expense_categories.json` | over 85%, NFR-4 |
| Amounts: full `/add-expense` line, expected candidates kept, expected question or amount | 50 | `backend/tests/eval/expense_amounts.json` | over 98%, NFR-5 |

Both run as a live test, marked like `test_capture_live.py`, never in CI. The
live run happens in slice 1 (T-1.14). These two JSON files are fixtures, not
code, and are the only repository files written before approval.

## 7. Definition of done, for the feature

- Every task in 04.1 to 04.3 is shipped or explicitly dropped in the dev log.
- NFR-1: T7 boundary tests pass for read, edit, delete, summary and search.
- NFR-2 and NFR-3 measured and recorded in the dev log.
- NFR-4 and NFR-5 evaluation results recorded in the dev log.
- NFR-6: totals equal the sum of stored paise in every summary test.
- NFR-7: the logging test passes with description and amount in every logged
  field.
- The design matches the canvas, or a change record says why not.
- `index.md` shows 006 as shipped.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-10-02 | Created as the index, with sub-plan 4.1 drafted and both evaluation sets drafted | Build plan approved; user asked to proceed | pending |
| 2026-10-02 | Approved | User: "approved, commit and start building slice 1" | user |
