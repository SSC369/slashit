---
doc: design
feature: 011-proactive-slashit
title: Proactive Slashit
stage: 2
status: draft
owner: user
created: 2026-09-17
updated: 2026-09-17
approved_on: null
supersedes: null
---

# Design — Proactive Slashit

> **Gate skipped.** No approved Epic (stage 0), no approved PRD (stage 1). Drawn
> ahead of both at the user's explicit direction on 2026-09-17, per
> [`CLAUDE.md`](../CLAUDE.md) §2. Nothing here is approved.

Context: PRD not written. Sourced to
[the V1 intake](../product/intake/2026-09-08-personal-jarvis-v1.md) §31, §28.
Canvas: none. Hand-drawn artboards, not Claude Design exports.
Exports: [`./assets/canvas/proactive-design.html`](./assets/canvas/proactive-design.html)

> **No FR ids exist yet.** Serves cites intake sections. Re-point at real FR
> numbers when the PRD is written.

## 0. What this reuses unchanged

Everything not listed in §2 comes from 001's approved system and is not redrawn
here: the command bar and palette, capture-in-flight, the pending-question
state, the record table, record detail, record edit, delete confirmation, the
shared `EdgeStates`, every colour and type token, the mobile bottom bar and the
dark values. This epic's artboards show only what 001 does not already answer.

## 1. Design intent

This is the only epic where Slashit speaks without being asked, which makes it
the easiest one to make people resent. Three rules hold it. Every suggestion
shows the record it came from, in a "because" line, so it never feels like
surveillance. Nothing is ever created, edited or deleted without a click.
And off is a real, one-click option from every single suggestion — not buried in
settings. A feature that cannot be dismissed permanently will be tolerated at
best.

## 2. Screen inventory

| Screen | Purpose | Serves | Artboard |
|---|---|---|---|
| Suggestions | Slashit speaking first, on Home | §31 | `Suggestions` |
| Control | Frequency, count, and permanently silenced kinds | §31 | `Control` |
| States | Five required states, including a deliberate silent failure | — | `States` |

## 3. Flows

| Flow | Entry | Steps | Exit | Serves |
|---|---|---|---|---|
| Notice | Home | Suggestions render below the greeting, after everything else | Act, defer, or silence | §31 |
| Act | A suggestion | One click; the record is created, undoably | Confirmation with undo | §31, §35 |
| Silence | A suggestion | "Never for …" removes that whole kind | Listed in Settings, reversible | §31 |

## 4. States

### Suggestions

| State | What the user sees | Copy |
|---|---|---|
| **Empty** | One line under the heading. No illustration | "Nothing that needs your attention right now." |
| Loading | Skeletons, resolving after the rest of Home | — |
| **Error** | **The section is not rendered at all. No banner** | — |
| Success, after acting | Green note with an undo | "Task added: **Renew insurance**, due 27 Sep. Undo" |
| No permission | Not reachable. Computed per account, never over records the user cannot see | — |

The silent failure is deliberate and is the only one in the product. Nothing was
asked for, so nothing is owed an explanation, and an error banner for an
unrequested feature is pure noise. The empty state is one line for the same
reason: a section that must always look full will fill itself with filler.

## 5. Responsive behaviour

| Breakpoint | Layout change |
|---|---|
| Mobile (390px) | Suggestion actions wrap to their own row under the because-line. "Never for …" moves into an overflow, since three buttons do not fit |
| Tablet | No distinct layout |
| Desktop | 760px column, below the greeting and tiles |

## 6. Design system deltas

| Change | Kind | Token or component | Why existing one does not fit |
|---|---|---|---|
| Suggestion card | added | component | Amber left rule marks it as unprompted. 004's answer block uses blue for asked-for speech; the distinction is the point |
| Because-line | added | component | Cites the record behind the suggestion, above the actions |
| Three-action row | added | component | Act, defer, silence-forever. The third is what makes the pattern acceptable |
| Silenced-kind chips | added | component | Removable, in Settings |
| Count control | changed | `.seg` | Reused unchanged for 1 / 3 / 5 |

## 7. Accessibility

| Area | Decision |
|---|---|
| Contrast | Amber on `--surface` for the left rule; the because-line is `--ink3`, which passes at 11.5px |
| Keyboard path | Suggestions come after the tiles in the tab order — last, because they are least important |
| Screen reader labels | The section is a `region`, **`aria-live="off"`**. It must not announce itself: unprompted content interrupting a screen-reader user mid-task is exactly the harm this epic risks |
| Motion and reduced motion | None. Suggestions appear on load, never animate in |
| Focus order | Never takes focus. Nothing here was requested |

## 8. Copy

| Location | Text | Notes |
|---|---|---|
| Section heading | "Slashit noticed" | Not "For you", not "Insights". Says who is speaking |
| Because-line | "Because you told me `Insurance renews 27 September` on 8 Sep, and nothing references it." | Always cites the source record and its date |
| Third action | "Never for renewals" | Names the kind, so the user knows exactly what they are silencing |
| Guarantee | "Slashit never creates, edits or deletes a record from a suggestion. Every one needs your click." | Stated on the surface, not only in settings |
| Off | "With suggestions off, Slashit goes back to answering only when asked. Nothing else changes." | |

## 9. Open questions

| # | Question | Owner | Answer |
|---|---|---|---|
| Q1 | What kinds of suggestion exist? Three are drawn (renewal without a task, stale task, goal complete). The real list is an epic-stage argument and drives everything | user, at epic | Open |
| Q2 | Are suggestions computed on load or on a schedule? Affects whether they can go stale between visits | user, at build plan | Open |
| Q3 | Home is the only surface drawn. Should suggestions ever reach email or a notification? **Drawn as never** — 003's channels exist and this deliberately does not use them | user, at epic | Open |
| Q4 | Does dismissing teach anything, or is "Never for …" the only signal? Drawn as the only signal, which is simple and predictable | user, at epic | Open |
| Q5 | §31 is nine lines of intake and this is a P2 epic. Is it in V1 at all, or the first thing cut? | user, at epic | Open |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-17 | Created, ahead of the epic and PRD gates | User asked for designs of all upcoming slices, to review later | pending |
