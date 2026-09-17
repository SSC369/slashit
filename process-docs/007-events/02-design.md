---
doc: design
feature: 007-events
title: Events
stage: 2
status: draft
owner: user
created: 2026-09-17
updated: 2026-09-17
approved_on: null
supersedes: null
---

# Design — Events

> **Gate skipped.** No approved Epic (stage 0), no approved PRD (stage 1). Drawn
> ahead of both at the user's explicit direction on 2026-09-17, per
> [`CLAUDE.md`](../CLAUDE.md) §2. Nothing here is approved.

Context: PRD not written. Sourced to
[the V1 intake](../product/intake/2026-09-08-personal-jarvis-v1.md) §22, §30.
Canvas: none. Hand-drawn artboards, not Claude Design exports.
Exports: [`./assets/canvas/events-design.html`](./assets/canvas/events-design.html)

> **No FR ids exist yet.** Serves cites intake sections. Re-point at real FR
> numbers when the PRD is written.

## 0. What this reuses unchanged

Everything not listed in §2 comes from 001's approved system and is not redrawn
here: the command bar and palette, capture-in-flight, the pending-question
state, the record table, record detail, record edit, delete confirmation, the
shared `EdgeStates`, every colour and type token, the mobile bottom bar and the
dark values. This epic's artboards show only what 001 does not already answer.

## 1. Design intent

Events are the lightest epic in V1 and the design should stay that way. Two
decisions carry it. An event with no time is all-day and says so, rather than
being given a silent midnight. And the list is grouped by day rather than
tabulated, because dates are what a person scans for — but it is a list of what
exists, not a calendar grid with empty days drawn in.

## 2. Screen inventory

| Screen | Purpose | Serves | Artboard |
|---|---|---|---|
| Capture | `/add-event`, all-day and timed | §22, §36 | `Capture` |
| Upcoming | Grouped by day | §22 | `Upcoming` |
| States | Five required states, plus the ambiguous date | — | `States` |

## 3. Flows

| Flow | Entry | Steps | Exit | Serves |
|---|---|---|---|---|
| Add | Capture | `/add-event …`, date and optional time resolved | Saved, undoable | §22, §35 |
| Review | Events | Upcoming, grouped by day; Past dims but keeps them | — | §22 |

## 4. States

### Upcoming

| State | What the user sees | Copy |
|---|---|---|
| Empty | Centered serif line and a command to try | "Nothing coming up" |
| Loading | Day heading and row skeletons | — |
| Error | Red note | "Events could not be loaded." |
| Success | Day groups, serif day number, event rows | — |
| Past | Same shape at 62% opacity, never hidden | — |
| No permission | Not reachable. Per-account behind sign-in | — |

### Capture, the failure unique to events

| State | What the user sees | Copy |
|---|---|---|
| Ambiguous year | Amber note, nothing saved, the likely answer offered | "\"October 12\" has already passed this year. Did you mean **2027**? Nothing is saved yet." |

## 5. Responsive behaviour

| Breakpoint | Layout change |
|---|---|
| Mobile (390px) | Day headings stay; the time column drops above the title rather than beside it |
| Tablet | No distinct layout |
| Desktop | One 720px column |

## 6. Design system deltas

| Change | Kind | Token or component | Why existing one does not fit |
|---|---|---|---|
| Day group heading | added | component | Serif day number plus weekday label. Today's number takes the blue token |
| Event row | added | component | Time column plus title. 001's record row has no time gutter |
| All-day treatment | added | convention | The time column reads "All day" in `--ink3`, never a rendered 12:00 AM |
| Past dimming | added | convention | 62% opacity. 001 has no concept of a record that is over |

## 7. Accessibility

| Area | Decision |
|---|---|
| Contrast | **Past events at 62% opacity fall below 4.5:1 and this is a known defect in the drawing.** Fix by using `--ink3` for past text rather than opacity on the whole row. Recorded as Q3 |
| Keyboard path | Day groups are headings; events are a list under each |
| Screen reader labels | Each event announces its full date, not just the time, because the day heading is visual grouping the reader may not carry |
| Motion and reduced motion | None |
| Focus order | Tabs, then the first upcoming event |

## 8. Copy

| Location | Text | Notes |
|---|---|---|
| All-day footer | "No time was given, so this is all day. Add one any time." | Names the inference |
| Empty-day note | "Days with nothing on them are not drawn. This is a list of what exists, not a calendar grid." | Sets the expectation once |
| Ambiguous year | "\"October 12\" has already passed this year. Did you mean 2027? Nothing is saved yet." | |

## 9. Open questions

| # | Question | Owner | Answer |
|---|---|---|---|
| Q1 | **This epic's Upcoming and 010's Upcoming view (§30) are the same surface.** 010's is drawn as superseding this one. Which lands first, and does 007 ship a view at all, or only the record type? | user, at epic | Open |
| Q2 | Do events have durations, or only a start? Drawn as start only, per §22's field list | user, at PRD | Open |
| Q3 | Past-event dimming fails contrast as drawn. Switch to a token rather than opacity | user, at design review | Open |
| Q4 | Can an event carry a reminder directly, or must the user create both? An obvious link to 003, not specified anywhere | user, at epic | Open |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-17 | Created, ahead of the epic and PRD gates | User asked for designs of all upcoming slices, to review later | pending |
