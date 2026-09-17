---
doc: design
feature: 006-expenses
title: Expenses
stage: 2
status: draft
owner: user
created: 2026-09-17
updated: 2026-09-17
approved_on: null
supersedes: null
---

# Design — Expenses

> **Gate skipped.** No approved Epic (stage 0), no approved PRD (stage 1). Drawn
> ahead of both at the user's explicit direction on 2026-09-17, per
> [`CLAUDE.md`](../CLAUDE.md) §2. Nothing here is approved.

Context: PRD not written. Sourced to
[the V1 intake](../product/intake/2026-09-08-personal-jarvis-v1.md) §14.
Canvas: none. Hand-drawn artboards, not Claude Design exports.
Exports: [`./assets/canvas/expenses-design.html`](./assets/canvas/expenses-design.html)

> **No FR ids exist yet.** Serves cites intake sections. Re-point at real FR
> numbers when the PRD is written.

## 0. What this reuses unchanged

Everything not listed in §2 comes from 001's approved system and is not redrawn
here: the command bar and palette, capture-in-flight, the pending-question
state, the record table, record detail, record edit, delete confirmation, the
shared `EdgeStates`, every colour and type token, the mobile bottom bar and the
dark values. This epic's artboards show only what 001 does not already answer.

## 1. Design intent

An expense is a task with a number on it, so almost nothing here should be new.
The two things that are: money has to be unambiguous, and a list of expenses is
useless without a total. Numbers are tabular-lined mono so columns of figures
compare by eye, and Slashit never converts currencies — it keeps a total per
currency rather than inventing a rate it cannot justify.

## 2. Screen inventory

| Screen | Purpose | Serves | Artboard |
|---|---|---|---|
| Capture | `/add-expense`, amount and currency resolved | §14, §36 | `Capture` |
| Summary | The aggregate 001 has no pattern for | §14 | `Summary` |
| States | Five required states, plus mixed currency | — | `States` |

## 3. Flows

| Flow | Entry | Steps | Exit | Serves |
|---|---|---|---|---|
| Record | Capture | `/add-expense …`, amount, category and date resolved, card confirms | Saved, undoable | §14, §35 |
| Review | Expenses | Period tabs, category breakdown, the list beneath | — | §14 |

## 4. States

### Summary

| State | What the user sees | Copy |
|---|---|---|
| Empty | Centered serif line and a command to try | "No expenses this month" |
| Loading | Total block and rows as skeletons at real height | — |
| Error | Red note above the list. The list still renders | "The summary could not be calculated. Your expenses are listed below, unaffected." |
| Success | Total, proportion bar, category rows, then the table | — |
| Mixed currency | Second total beside the first, never summed | "Slashit does not convert currencies. Totals are kept per currency so nothing is invented." |
| No permission | Not reachable. Per-account behind sign-in | — |

### Capture, the one failure unique to expenses

| State | What the user sees | Copy |
|---|---|---|
| No amount found | Amber note, nothing saved | "No amount found in that. Add one, or say the number on its own." |

## 5. Responsive behaviour

| Breakpoint | Layout change |
|---|---|
| Mobile (390px) | Total block full width, proportion bar stays, category rows stack. The table becomes 001's stacked record rows with the amount right-aligned on the first line |
| Tablet | No distinct layout |
| Desktop | Summary and table in one 820px column |

## 6. Design system deltas

| Change | Kind | Token or component | Why existing one does not fit |
|---|---|---|---|
| Tabular numerals | added | type rule | Mono with `tabular-nums`. 001 reserves mono for commands and captured text; this widens that rule, deliberately, because columns of money must align |
| Total block | added | component | Serif number at 32px. No existing component displays one figure as the subject |
| Proportion bar | added | component | Category split in one row |
| Category row | added | component | Swatch, name, amount, percent |
| Category swatch | added | component | Reuses existing semantic hues as categorical colours, which is a **misuse worth naming**: amber means "command" in 001, not "food". See Q3 |

## 6a. Dark theme

Added 2026-09-17, alongside the rest of this design. Dark reuses **001's
approved palette unchanged** — the eighteen token pairs in its `DarkTokens`
artboard, which the shipped `frontend/src/design-system/tokens.css` already
carries byte-for-byte. **This epic adds no colour token**, and it inherits
001's one dark-specific rule: a primary button inverts to a light blue field
with dark ink on it, never white.

Dark artboards on the canvas: `Summary`. States and mobile panels are not
redrawn in dark — they are the same components on the same tokens, and 001
took the same representative-subset approach rather than doubling its canvas.

## 7. Accessibility

| Area | Decision |
|---|---|
| Contrast | Unchanged. The swatch colours are existing tokens |
| Keyboard path | Period tabs are a tab list. The table follows 001's existing row semantics |
| Screen reader labels | Amounts are announced with the currency spelled out, not the symbol. The proportion bar is `aria-hidden`; the category rows beneath carry the same data as text |
| Motion and reduced motion | None |
| Focus order | Period tabs, then the table |

## 8. Copy

| Location | Text | Notes |
|---|---|---|
| Capture footer | "Currency from your settings · \"yesterday\" resolved against Asia/Kolkata" | Names both inferences in one line |
| Mixed currency | "Slashit does not convert currencies. Totals are kept per currency so nothing is invented." | |
| No amount | "No amount found in that. Add one, or say the number on its own." | |

## 9. Open questions

| # | Question | Owner | Answer |
|---|---|---|---|
| Q1 | "Expense summaries" is the whole of §14 on this subject. Is the drawn month/category breakdown the intent, or is something smaller wanted? **This is the one genuinely undefined thing in the epic** | user, at epic | Open |
| Q2 | Are categories fixed, model-chosen, or user-defined? Drawn as model-chosen, like 004's memory categories | user, at epic | Open |
| Q3 | Reusing semantic hues as categorical colours conflicts with 001's token meanings. Add a categorical ramp, or accept the overlap? | user, at design review | Open |
| Q4 | Is there a budget or limit concept in V1? Nothing in §14 says so; nothing is drawn | user, at epic | Open |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-17 | Created, ahead of the epic and PRD gates | User asked for designs of all upcoming slices, to review later | pending |
| 2026-09-17 | Dark theme added (§6a), reusing 001's approved palette unchanged | User asked for dark designs alongside the light ones | pending |
