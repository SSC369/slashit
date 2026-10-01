---
doc: epic
feature: 006-expenses
title: Expenses
stage: 0
status: approved
owner: user
created: 2026-10-02
updated: 2026-10-02
approved_on: 2026-10-02
supersedes: null
---

# Epic — Expenses

> **Approved** by @user on 2026-10-02. Locked — changes require a change record (§7).

Context: [Product](../product/product.md) · [V1 features](../product/v1-features.md)

About twenty lines over the 150-line budget, for eleven questions. Each lists
its options and answer, and none repeats another.

## As supplied

> start the epic for 006 expenses

The requirement is the V1 product definition: §14, the expense card in §19, and
the `/add-expense 500` example in §35. It is cited here, not copied:
[intake](../product/intake/2026-09-08-personal-jarvis-v1.md#14-expense-records).
`v1-features.md` §3 scopes this epic to "Expenses §14, expense summaries". It
depends on 001 and 002, both built. 005 is in dev, and its FR-11 requires every
new record type to be searchable from the day it ships.

## Problem

Product segment one keeps spending in an expense tracker or a spreadsheet. That
split is the fragmentation Slashit exists to remove. Each separate place is
another app to open, and the money spent never sits next to the tasks and plans
that caused it.

Every record type built so far is an action or a fact. None is a number that
adds up. "How much did I spend on food this month?" has no answer in Slashit
today. Getting that answer from a spreadsheet means categorising every line by
hand, and that upkeep is the step the system-averse segment skips.

## What this feature is

A new record type, the expense: an amount in rupees, a description, a category
and the date it was spent. The user records one with `/add-expense ₹850 dinner
yesterday`. Slashit pulls out the amount, description and date, picks a category,
and creates the record immediately. If the amount or the description is missing,
Slashit asks one question first. Expenses appear under Records in an Expenses
view, with a detail card for each and edit and delete there.
`/expenses this month` returns totals by category and a grand total for the
period. The Expenses view shows the same totals. It is a record type plus
arithmetic, not a budgeting tool.

## Requirements in detail

| Area | What it has to do | Why it matters | Notes |
|---|---|---|---|
| Capture | `/add-expense <text>` creates an expense with amount, description, category and date pulled from the text | Source §3.2 gives this exact example | Extraction rides on 001's capture pipeline |
| Amount | A positive rupee amount, kept to the paisa. Reads `₹850`, `850`, `₹1,200`, `Rs 500`, `1.2k` | Totals are only as good as the parsing | Per Q1, ₹ only. A bare number is read as rupees. This looks simple and is not: "2 coffees 180" holds a quantity and an amount. Per Q6, Slashit asks which number is the amount |
| Other currencies | Text with a clearly different currency, such as `$20`, is refused with a one-line reason saying rupees only for now | Saving $20 as ₹20 silently corrupts every total | Per Q7. Conversion to ₹ is pending and tracked as a sub-plan of epic 012. It needs an exchange-rate source the user configures later |
| Missing amount | `/add-expense dinner` asks "How much was it?" | The confirmation model asks when a required field is missing | Uses 001's non-blocking pending question (FR-36) |
| Missing description | `/add-expense 500` asks "What was the expense for?" | Source §35 gives this exact example | Same mechanism |
| Date | Defaults to today. Relative dates ("yesterday", "last Friday") resolve in the user's timezone | Source §3.2. Expenses are mostly logged after the fact | Reuses 001 FR-5. A future date is shown as read and the user confirms it or picks another from a calendar, per Q5 revised |
| Category | One category per expense, chosen by Slashit from a fixed set and editable afterwards | Source §14 and §19 show a category on every expense | Per Q2 and Q4: Food, Transport, Shopping, Bills, Health, Entertainment, Travel, Other. A failed or unsure classification saves as Other and never blocks creation |
| Expenses view | A list under Records showing date, description, category and amount, newest first | Principle 1. Source §11, §14 | Built on 001's records view. Filter by category and by period, and search by words |
| All view | Expenses appear in the All records view with the amount in the status column | Source §12 draws exactly this | |
| Detail | Shows amount, description, category, date, origin and created time, with Edit and Delete | Source §19 draws this card | |
| Edit and delete | From the detail and the Expenses view only, never by command | Per Q3, matches 001 FR-24 | Delete is a soft delete, the product rule in §4 |
| Summaries | `/expenses <period>` returns per-category totals and a grand total. The Expenses view shows the same totals for the period it is filtered to | Source §14 draws `/expenses this month`. Principle 2: AI and views show one truth | Per Q8 and Q10. Periods: today, this or last week, this or last month, a named month, this year. Soft-deleted expenses never count |
| `/expenses` without a period | Shows this month's totals | The common case | Per Q9 |
| Empty period | "No expenses recorded for September" with the period named, never "₹0" in a table | A table of zeros reads as a bug | |
| Search | Expenses are found by personal search from the day they ship | 005's FR-11 binds this | Search by description and category, and by exact amount, so "850" finds every ₹850 expense, per Q11 |
| Origin | Every expense stores origin and creation time | Principle 5 | Always "command" in V1 |
| Isolation | Only the owner's expenses are read, summed or sent to a prompt | Principle 7 | Spending is financial data. Totals must be scoped per user in the query, not filtered afterwards |

## Pros

- Serves segment one directly. The intake names expense trackers as one of the
  apps Slashit replaces.
- Cheap on the foundation. One extraction call per capture, no scheduler, no
  notifications, no new kind of action.
- Introduces the first totals in the product. 010's Today and home dashboard
  depend on 006 and will want "spent this week".
- Gives 005 and later proactive help (011) something new: money, which is part
  of the context behind most plans.
- Low risk to existing data. It adds a record type and changes no behaviour of
  tasks, reminders or memories.

## Cons

- The first type where a wrong field is a wrong number. A misread amount does
  not just look odd, it corrupts every total it falls into, and the user may
  never notice.
- Category quality decides whether summaries are worth reading. An expense
  wrongly filed as Shopping when it was Food makes the breakdown misleading,
  and correcting it is manual.
- Financial data raises the sensitivity bar again, after memories. Every
  description goes to the model for extraction, which sharpens product Q10.
- ₹ only shuts out a foreign spend until epic 012 adds conversion. That work
  depends on an exchange-rate source nobody has configured yet.
- A fixed category set will not fit everyone. Users who want "Kids" or "Pets"
  get Other, and Other grows into a junk drawer.
- Pressure toward budgeting is built in. Once totals exist, budgets, limits and
  alerts are the obvious next ask, and the product doc rules them out.

## Best practices and prior art

| Product | How they do it | What to take | What to avoid |
|---|---|---|---|
| Splitwise | Suggests a category from the description as the user types, editable before saving | Category inferred from words, always correctable | Group splitting, which is out of scope here |
| Walnut, now axio | Builds the expense list by reading bank SMS on the phone | Proof that Indian users want expenses captured without typing forms | Reading bank messages is a banking integration, a product non-goal |
| YNAB | Envelope budgeting: every rupee is assigned a job before it is spent | Nothing for V1 | Upfront structure and daily upkeep, the exact thing the system-averse segment drops |
| Google Sheets expense templates | One row per expense, sum by category with a formula | The summary shape users already know: category, total, grand total | Manual categorising and a separate place to open |

## Alternatives considered

| Option | What it gives | What it costs | Verdict |
|---|---|---|---|
| Do nothing, log spends as notes or tasks | No new type | Nothing adds up, and expense trackers stay in use | Rejected |
| Expenses without summaries | Smallest slice | Leaves source §14's main example undone. A list of amounts nobody totals | Rejected |
| Summaries by command only, with the view as a plain list | Less view work | Breaks principle 2: the AI would know a total the view cannot show | Rejected by Q8 |
| Totals plus trends or charts | Richer view | Edges into financial planning, a product non-goal. Waits for usage | Rejected for V1 |
| Convert other currencies to ₹ on capture | Travellers covered, totals stay in one currency | An exchange-rate source, and a rate date per expense | Deferred to epic 012 by Q7. Store the ₹ value only |
| User-defined categories | Fits every life | More UI, and classification gets less predictable | Rejected by Q2. Revisit if Other grows large |
| Recurring expenses, such as rent | Less typing for fixed costs | 003's recurrence machinery applied to money, and it creates records the user did not type | Deferred. See What this is not |

## Risks and unknowns

| Risk | Likelihood | Impact | What would tell us early |
|---|---|---|---|
| Amount misread, such as "1.2k" or "Rs 1,20,000" in Indian grouping | medium | high | A fixture set of tricky inputs in the eval, and how often users edit the amount after saving |
| Category wrong often enough that users distrust the summary | medium | medium | Share of expenses whose category is edited after save |
| Other becomes the largest category | medium | medium | Other's share of the total, per user |
| Summaries slow down as a user's expense count grows | low | low | Summary latency split by expense count |
| Expense text reaching the model breaches the bar product Q10 sets | unknown | high | Already open as product Q10 |

## Open questions

| # | Question | Options | Answer |
|---|---|---|---|
| ~~Q1~~ | Which currency? | ₹ only · one home currency per user · currency per expense | **₹ only**, user 2026-10-02. Closes product Q6 for V1 on approval |
| ~~Q2~~ | How are categories set? | Fixed, auto-assigned · fixed plus user-added · free-form | **Fixed set, auto-assigned, editable**, user 2026-10-02 |
| ~~Q3~~ | Edit or delete by command? | Detail view only · add `/delete-expense` | **Detail view only**, user 2026-10-02 |
| ~~Q8~~ | How much do summaries do? | Category totals per period · command only · totals plus trends | **Category totals per period, in the command and the view**, user 2026-10-02 |
| ~~Q4~~ | Which fixed categories? | Eight · ten, adding Rent and Education · four | **Eight: Food, Transport, Shopping, Bills, Health, Entertainment, Travel, Other**, user 2026-10-02 |
| ~~Q5~~ | Can an expense be dated in the future? | No, ask again · allow it | **Revised 2026-10-02: yes, after confirming.** Slashit names the date it read, such as "next Saturday" as Sat 10 Oct, and the user confirms it or picks another date from a calendar. Only future dates ask; past ones save at once. Was "no, ask again" |
| ~~Q6~~ | Text holding a quantity and an amount, such as "2 coffees 180"? | Larger number is the amount · ask which · let the model decide | **Ask which number is the amount**, user 2026-10-02. Not the recommended option |
| ~~Q7~~ | Text in another currency, such as `$20 lunch`? | Refuse · ask for the rupee amount · convert · save as rupees | **Convert to ₹ and store the ₹ value only, but later.** The user will configure an exchange-rate source; until then such text is refused with a reason. Tracked as a sub-plan of epic 012, user 2026-10-02 |
| ~~Q9~~ | What does `/expenses` with no period show? | This month's totals · latest ten · ask | **This month's totals**, user 2026-10-02 |
| ~~Q10~~ | Which periods do summaries accept? | Common set · common set plus any range · this month only | **Today, this or last week, this or last month, a named month, this year**, user 2026-10-02 |
| ~~Q11~~ | Does search find an expense by its amount? | Exact match · words only | **Yes, as an exact match**, user 2026-10-02 |

## What this is not

- Not budgeting. No budgets, limits, alerts or savings goals. This is a product
  non-goal.
- Not income. Money in, refunds and net balance are out.
- Not a bank link. No reading statements, SMS or receipts.
- Not split or shared expenses. One account, one owner.
- Not recurring expenses. Rent typed every month is typed every month.
- Not plain-language capture. "I spent ₹850 on dinner", from §3.3, stays
  refused until plain-language capture returns, per 001 FR-9.
- Not receipt photos or attachments.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-10-02 | Created. Q1, Q2, Q3 and Q8 answered before drafting, each with the recommended option | User asked to start the epic | pending |
| 2026-10-02 | Q4 to Q7 and Q9 to Q11 answered. Q6 departs from the recommendation: ask which number is the amount. Q7 adds currency conversion as pending work in epic 012. Requirements, cons, alternatives and risks updated | User answered the open questions | user |
| 2026-10-02 | Approved | User: "commit and proceed with next" | user |
| 2026-10-02 | Q5 revised: a future date is allowed once the user confirms the date Slashit read or picks another from a calendar. Only future dates ask. Stale: PRD FR-8 and FR-21, design `ExpenseAsk`, `DetailStates` | User asked for the resolved date to be confirmed with a custom date picker | user, 2026-10-02 |
