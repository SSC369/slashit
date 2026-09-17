---
doc: design
feature: 010-daily-control
title: Daily Control
stage: 2
status: draft
owner: user
created: 2026-09-17
updated: 2026-09-17
approved_on: null
supersedes: null
---

# Design — Daily Control

> **Gate skipped.** No approved Epic (stage 0), no approved PRD (stage 1). Drawn
> ahead of both at the user's explicit direction on 2026-09-17, per
> [`CLAUDE.md`](../CLAUDE.md) §2. Nothing here is approved.

Context: PRD not written. Sourced to
[the V1 intake](../product/intake/2026-09-08-personal-jarvis-v1.md) §29, §30, §32, §33.
Canvas: none. Hand-drawn artboards, not Claude Design exports.
Exports: [`./assets/canvas/daily-design.html`](./assets/canvas/daily-design.html)

> **No FR ids exist yet.** Serves cites intake sections. Re-point at real FR
> numbers when the PRD is written.

## 0. What this reuses unchanged

Everything not listed in §2 comes from 001's approved system and is not redrawn
here: the command bar and palette, capture-in-flight, the pending-question
state, the record table, record detail, record edit, delete confirmation, the
shared `EdgeStates`, every colour and type token, the mobile bottom bar and the
dark values. This epic's artboards show only what 001 does not already answer.

## 1. Design intent

This epic assembles everything the others recorded into one answer to "what is
my situation". Today is that answer for the next few hours; Upcoming is the same
answer stretched over a month; Home is where you land. The honest part of this
design is that it cannot be done without changing 001: three flat rail items
become nine in two groups, and the landing screen stops being Capture. That is
drawn explicitly rather than smuggled in.

## 2. Screen inventory

| Screen | Purpose | Serves | Artboard |
|---|---|---|---|
| Today | `/today`, assembled from every record type | §29 | `Today` |
| Upcoming | `/upcoming`, a timeline | §30 | `Upcoming` |
| Home | The dashboard and the new landing screen | §32 | `Home` |
| Navigation change | 001's rail beside what this needs | §33 | `NavigationChange` |
| States | Five required states, per tile | — | `States` |

## 3. Flows

| Flow | Entry | Steps | Exit | Serves |
|---|---|---|---|---|
| Land | Sign in | Home: greeting, command bar, tiles | Anywhere | §32 |
| Today | `/today` or the rail | One page, grouped by kind | Act in place | §29 |
| Upcoming | `/upcoming` or the rail | Timeline, dated groups | Record detail | §30 |

## 4. States

### Home

| State | What the user sees | Copy |
|---|---|---|
| **Empty** | Greeting and command bar. No illustration, no "get started" | "Nothing is due today, and nothing is coming up this week." |
| Loading | **Per tile, not per page.** Each tile skeletons independently | — |
| **Partial** | The failed tile shows its own inline error; the rest render | "Expenses could not be loaded. Retry" |
| Error | Whole-page note with a way out | "Home could not be assembled. Your records are unaffected — go to Capture." |
| Success | Greeting, command bar, Today tile, This-month tile, Goals tile | — |
| No permission | Not reachable. Signed-out users are redirected to 002's sign-in | — |

An empty day is deliberately not treated as a problem. A dashboard that nags
when there is nothing to do teaches people to ignore it.

## 5. Responsive behaviour

| Breakpoint | Layout change |
|---|---|
| Mobile (390px) | Tiles stack in one column, Today first. The rail's two groups become the bottom bar's five slots, so **the group structure does not survive mobile** — see Q3 |
| Tablet | Tiles in one column at full width |
| Desktop | 1.35fr / 1fr two-column grid, 940px |

## 6. Design system deltas

| Change | Kind | Token or component | Why existing one does not fit |
|---|---|---|---|
| **Grouped rail** | **changed** | **`.rail`, `.nav`** | **001's rail is three flat items. This adds group labels and nine items. Requires a change record against 001** |
| **Landing route** | **changed** | **navigation** | **Capture stops being `/`. This contradicts 001's stated intent that capture is the front door** |
| Dashboard tile | added | component | Header, body, independent loading and error |
| Section heading | added | component | Label, rule, count. Used across Today and Home |
| Checkable item row | added | component | Checkbox, title, optional time. 001's rows are not actionable in place |
| Timeline | added | component | Dated groups on a rule, with a now-marker |
| Greeting | added | component | Serif, 34px, time-of-day aware |
| Stat figure | added | component | Serif number as the subject of a tile |

## 6a. Dark theme

Added 2026-09-17, alongside the rest of this design. Dark reuses **001's
approved palette unchanged** — the eighteen token pairs in its `DarkTokens`
artboard, which the shipped `frontend/src/design-system/tokens.css` already
carries byte-for-byte. **This epic adds no colour token**, and it inherits
001's one dark-specific rule: a primary button inverts to a light blue field
with dark ink on it, never white.

Dark artboards on the canvas: `Home`, `Today`. States and mobile panels are not
redrawn in dark — they are the same components on the same tokens, and 001
took the same representative-subset approach rather than doubling its canvas.

## 7. Accessibility

| Area | Decision |
|---|---|
| Contrast | Unchanged from 001. No new colours |
| Keyboard path | Home's command bar takes focus on load, so the keyboard path from 001 survives the landing change. Tiles are regions with headings |
| Screen reader labels | Each tile is a `region` with an `aria-label`. A failed tile announces its own error rather than one page-level alert. Checkable rows are real checkboxes |
| Motion and reduced motion | None |
| Focus order | Greeting, command bar, then tiles in visual order |

## 8. Copy

| Location | Text | Notes |
|---|---|---|
| Greeting | "Good evening, Jordan." | Time-of-day aware. > Assumption: not specified; flagged as Q4 |
| Summary line | "Two tasks left, one event at 7, and a renewal coming up in ten days." | One sentence assembled from the tiles below it |
| Empty day | "Nothing is due today, and nothing is coming up this week." | Stated plainly, not as a prompt to do more |
| Whole-page error | "Home could not be assembled. Your records are unaffected — go to Capture." | Always offers the surface that does work |

## 9. Open questions

| # | Question | Owner | Answer |
|---|---|---|---|
| Q1 | **Does Home displace Capture as the landing screen?** 001's design intent is that the command bar is the front door. This is a product decision, not a design one, and it is the largest question in the epic | user, at epic | Open |
| Q2 | 007's Upcoming events and §30's Upcoming view are the same surface. Drawn as one, here. Confirm, and record it against 007 | user, at epic | Open |
| Q3 | The rail's Views/Records grouping has no mobile equivalent — the bottom bar holds five items flat. What gets cut on mobile? | user, at design review | Open |
| Q4 | Is a time-of-day greeting wanted, or is it noise? | user, at PRD | Open |
| Q5 | Which tiles does Home show, and can the user choose? Drawn as fixed: Today, This month, Goals | user, at epic | Open |
| Q6 | 010 depends on 003, 006, 007 and 008. What does Home show when some have not shipped — hide the tile, or show it empty? | user, at epic | Open |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-17 | Created, ahead of the epic and PRD gates | User asked for designs of all upcoming slices, to review later | pending |
| 2026-09-17 | Dark theme added (§6a), reusing 001's approved palette unchanged | User asked for dark designs alongside the light ones | pending |
