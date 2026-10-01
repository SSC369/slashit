---
doc: prd
feature: 006-expenses
title: Expenses
stage: 1
status: approved
owner: user
created: 2026-10-02
updated: 2026-10-02
approved_on: 2026-10-02
supersedes: null
---

# Epic PRD — Expenses

> **Approved** by @user on 2026-10-02. Locked — changes require a change record (§7).

Context: [Epic](./00-epic.md) · [Product](../product/product.md) ·
[001 PRD](../001-capture-and-records-foundation/01-prd.md) ·
[005 PRD](../005-personal-search-and-context/01-prd.md)

Over the 150-line budget by about fifty lines: capture alone has fifteen
separate testable behaviours, from reading amounts to the questions it asks.

## 1. Problem

Spending lives in a separate expense tracker or spreadsheet, apart from
everything else Slashit holds. No record in Slashit is a number that adds up, so
"how much did I spend on food this month?" has no answer. Getting one elsewhere
means categorising every line by hand, which is the upkeep the system-averse
user drops.

## 2. Users and jobs

| User | Job to be done | Today's workaround |
|---|---|---|
| The fragmented individual | Log a spend in one line, in the same place as their tasks and plans | An expense app or a spreadsheet, opened separately |
| The same user, at month end | See where the money went, by category, for a period | Sum a spreadsheet by hand, or a tracker's report |
| The system-averse user | Get a category on every spend without choosing one | Skip categories, so totals mean little |

## 3. Goals

| # | Goal | What we measure |
|---|---|---|
| G1 | Users log spends in Slashit | Expenses saved per active user per week |
| G2 | Users read their totals | Summaries viewed per active user per week, by `/expenses` or the view |
| G3 | Categories are trusted | Share of expenses whose category is edited after save |
| G4 | Amounts are read right | Share of expenses whose amount is edited after save |

> Assumption: no numeric targets, following the product decision of
> 2026-09-08 (`product.md` §9). Every goal is instrumented from launch.

## 4. Non-goals

- Budgets, limits, alerts or savings goals. A product non-goal.
- Income, refunds or a net balance.
- Reading bank statements, SMS or receipts.
- Split or shared expenses.
- Recurring expenses.
- Plain-language capture. "I spent ₹850 on dinner" stays under 001's FR-9.
- Currencies other than ₹. Conversion is pending work in epic 012.
- Trends, comparisons or charts across periods.

## 5. User stories

- **US-1.** As a user, I type `/add-expense ₹850 dinner yesterday`, so that the
  spend is recorded with its amount, category and date without a form.
- **US-2.** As a user, when I leave out the amount or what it was for, I am
  asked once, so that no expense is saved half-filled.
- **US-3.** As a user, I open my expenses and see every one with its date,
  description, category and amount, so that nothing is hidden from me.
- **US-4.** As a user, I type `/expenses this month`, so that I see what I spent
  by category and in total.
- **US-5.** As a user, I fix an expense's amount, category, description or date,
  or delete it, so that my totals are right.
- **US-6.** As a user, I search "850" or "uber", so that I find a spend without
  scrolling.

## 6. Functional requirements

### Capture

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-1 | `/add-expense <text>` saves an expense with amount, description, category and date taken from the text. It appears in command discovery | must | US-1 |
| FR-2 | The amount is a positive rupee value with up to two decimal places. `₹850`, `850`, `₹1,200`, `₹1,20,000`, `Rs 500` and `1.2k` are all read. A bare number is rupees. There is no upper limit | must | US-1 |
| FR-3 | Text with no amount asks "How much was it?", following 001's FR-8 | must | US-2 |
| FR-4 | Text with no description asks "What was the expense for?" | must | US-2 |
| FR-5 | Text with more than one candidate number, such as "2 coffees 180", asks which is the amount, offering each number as a choice | must | US-2 |
| FR-6 | Text with an amount in another currency, such as `$20`, is refused with one line saying Slashit records rupees only for now. The typed text is preserved | must | US-1 |
| FR-7 | The date defaults to today. Relative dates resolve in the user's timezone, following 001's FR-5 | must | US-1 |
| FR-8 | A date after today is shown as Slashit read it, such as "next Saturday" as Sat 10 Oct, and the user confirms it or picks any other date from a calendar. Nothing is saved until answered. A date today or earlier saves without asking | must | US-1 |
| FR-9 | Every expense carries one category from a fixed eight: Food, Transport, Shopping, Bills, Health, Entertainment, Travel, Other. Slashit assigns it on save | must | US-1 |
| FR-10 | When Slashit cannot decide a category, the expense is saved as Other. Category never causes a question | must | US-1 |
| FR-11 | The description keeps the user's words for what was bought, without the amount and date. Slashit does not rewrite them | must | US-1 |
| FR-12 | After saving, Slashit shows the amount, description, category and date where the user typed, following 001's FR-7 | must | US-1 |
| FR-13 | A description longer than 200 characters is refused with the limit stated, and the typed text is preserved | must | US-1 |
| FR-14 | When the model is unavailable, the save is refused as in 001's FR-35, and the typed text is preserved | must | US-1 |
| FR-15 | Questions from FR-3 to FR-5 and FR-8 do not block, following 001's FR-36 and FR-37 | must | US-2 |

> Assumption: FR-13's 200 characters. A spend description is short, and 004
> set 500 for a whole fact. Strike or change it in review.

### View, edit and delete

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-16 | The records view offers an Expenses filter listing every expense with its date, description, category and amount, newest by date first | must | US-3 |
| FR-17 | Expenses can be filtered by category and by period. Periods are those in FR-23 | must | US-3 |
| FR-18 | The Expenses filter shows per-category totals and a grand total for the period it is filtered to | must | US-4 |
| FR-19 | In the All records view, an expense shows its amount where other types show a status | must | US-3 |
| FR-20 | Opening an expense shows its amount, description, category, date, origin, creation time and last edit time, with Edit and Delete | must | US-3 |
| FR-21 | The user can edit amount, description, category and date. Editing the description leaves the category unchanged. FR-2 and FR-13 apply. Any date can be picked, past or future, without a further question | must | US-5 |
| FR-22 | Delete from the detail asks for confirmation, naming the amount and description. A deleted expense is soft-deleted, per `product.md` §4, and leaves every view, count and total. Expenses are never edited or deleted by command, following 001's FR-24 | must | US-5 |

> Assumption: FR-21 does not re-categorise on description edits, matching
> 004's FR-18. A stale category is fixed by editing it.

> Assumption: a future-dated expense counts in the period holding its date,
> so a confirmed Sat 10 Oct expense is in October's total from the day it is
> saved.

### Summaries

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-23 | `/expenses <period>` shows per-category totals and a grand total for the period. Accepted periods: today, this week, last week, this month, last month, a named month, this year | must | US-4 |
| FR-24 | `/expenses` with no period shows this month | must | US-4 |
| FR-25 | Categories with nothing spent are left out. Categories are ordered by total, largest first | must | US-4 |
| FR-26 | A period with no expenses says so, naming the period, such as "No expenses recorded in September" | must | US-4 |
| FR-27 | A period Slashit cannot read is refused, listing the accepted periods | must | US-4 |
| FR-28 | `/expenses` and the Expenses filter give the same totals for the same period | must | US-4 |

> Assumption: weeks start on Monday, and a named month without a year means the
> most recent one not after today. Strike either in review.

### Search

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-29 | Personal search finds expenses by description and category, from the day expenses ship, per 005's FR-11 | must | US-6 |
| FR-30 | A search that is a number matches expenses of exactly that amount | must | US-6 |

## 7. Non-functional requirements

| id | Requirement | Number | How it is measured |
|---|---|---|---|
| NFR-1 | A user's expenses are never readable by another user, in storage, in a total or in a model prompt | Zero incidents | Authorisation tests on every expense path, including summaries |
| NFR-2 | A save is confirmed, or its question shown, promptly | Under 8 s at p95, matching 001 and 004 | Server timing from submit to response |
| NFR-3 | `/expenses` and the Expenses filter respond promptly | Under 1 s at p95 for a user with 5,000 expenses | Load test |
| NFR-4 | Categories are right on everyday spends | Over 85% correct | Labelled evaluation set, built before build plan approval |
| NFR-5 | Amounts are read right | Over 98% correct, including Indian digit grouping and `k` | Labelled evaluation set, built before build plan approval |
| NFR-6 | Totals are exact | Zero rounding error to the paisa | Tests summing stored amounts |
| NFR-7 | Expense descriptions and amounts never appear in application logs or analytics events | Zero occurrences | Log and event review, and a test asserting it |

> 5,000 expenses is `estimate`: about five a day for three years. NFR-5's 98%
> was set by the user on 2026-10-02.

## 8. Success metrics

Instrumented from launch, reported weekly, no targets set. See section 3.

| Metric | Instrumented by | What it tells us |
|---|---|---|
| Expenses saved per active user per week | Save events | Whether logging spends earns a habit (G1, H1) |
| Summaries viewed per active user per week | `/expenses` and filter events | Whether totals are read (G2, H2) |
| Share of expenses with category edited | Edit events | Whether categories are trusted (G3) |
| Share of expenses with amount edited | Edit events | Whether amounts are read right (G4) |
| Other's share of all expenses | Save events | Whether the fixed eight fit |
| Foreign-currency refusals per week | FR-6 events | The case for epic 012's conversion |

## 9. Dependencies

| Dependency | Type | Owner | Status |
|---|---|---|---|
| Command capture, pending questions, timezone and the records view | internal | 001 | Built |
| An account that owns every expense | internal | 002 | Built |
| A model boundary with per-user attribution and quota | internal | 000 | Built |
| Personal search across record types | internal | 005 | In dev |
| Model provider data terms fit for financial data | vendor | user | Open as product Q10 |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| An amount is misread and skews totals unnoticed | medium | high | NFR-5, FR-5's question, FR-12 showing the amount after save |
| A huge typo, such as ₹85,000 for ₹850, stands with no limit to catch it | medium | medium | FR-12 shows the amount at save. Amount-edit metric |
| Categories are wrong often enough that summaries mislead | medium | medium | NFR-4, FR-21, category-edit metric |
| Other grows into a junk drawer | medium | medium | Other's-share metric. User-defined categories are the revisit |
| FR-5 asks too often on everyday text | medium | low | Count FR-5 questions per save once live |

## 11. Open questions

| # | Question | Blocks | Owner | Answer |
|---|---|---|---|---|
| ~~Q0a~~ | Largest amount? | PRD | user | **No limit**, 2026-10-02. FR-2 |
| ~~Q0b~~ | Model unavailable? | PRD | user | **Refuse, keep the text**, 2026-10-02. FR-14 |
| ~~Q0c~~ | Save latency? | PRD | user | **8 s at p95**, 2026-10-02. NFR-2 |
| ~~Q0d~~ | Category accuracy? | PRD | user | **Over 85%**, 2026-10-02. NFR-4 |
| ~~Q1~~ | Amount accuracy target for NFR-5? | build plan | user | **Over 98%**, 2026-10-02. NFR-5 |

## 12. Out of scope

- Budgets, income, bank links, splits, recurring expenses, charts. See section 4.
- Currency conversion. Epic 012.
- An `/edit-expense` or `/delete-expense` command.
- Receipt photos or attachments.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-10-02 | Created | Drafted after epic approval. Max amount, model-down behaviour, latency and category accuracy answered first | pending |
| 2026-10-02 | Q1 answered: amount accuracy over 98% | User answered | user |
| 2026-10-02 | Approved | User: "approved, go with next" | user |
| 2026-10-02 | FR-8 rewritten: a future date is confirmed or replaced from a calendar, no longer refused. FR-21 allows any date on edit. Stale: design, drafted, updated in the same change | Epic Q5 revised by the user | user, 2026-10-02 |
