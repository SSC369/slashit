---
doc: design
feature: 008-goals-and-projects
title: Goals and Projects
stage: 2
status: draft
owner: user
created: 2026-09-17
updated: 2026-09-17
approved_on: null
supersedes: null
---

# Design — Goals and Projects

> **Gate skipped.** No approved Epic (stage 0), no approved PRD (stage 1). Drawn
> ahead of both at the user's explicit direction on 2026-09-17, per
> [`CLAUDE.md`](../CLAUDE.md) §2. Nothing here is approved.

Context: PRD not written. Sourced to
[the V1 intake](../product/intake/2026-09-08-personal-jarvis-v1.md) §23, §24, §28.
Canvas: none. Hand-drawn artboards, not Claude Design exports.
Exports: [`./assets/canvas/goals-design.html`](./assets/canvas/goals-design.html)

> **No FR ids exist yet.** Serves cites intake sections. Re-point at real FR
> numbers when the PRD is written.

## 0. What this reuses unchanged

Everything not listed in §2 comes from 001's approved system and is not redrawn
here: the command bar and palette, capture-in-flight, the pending-question
state, the record table, record detail, record edit, delete confirmation, the
shared `EdgeStates`, every colour and type token, the mobile bottom bar and the
dark values. This epic's artboards show only what 001 does not already answer.

## 1. Design intent

Goals introduce hierarchy, and hierarchy is where products usually start feeling
like project management software. Three decisions keep it from happening.
Progress is derived from tasks and never typed in, so the number cannot lie. A
goal with nothing under it shows a dash rather than 0%, because zero claims a
measurement nobody took. And Slashit never marks a goal achieved on its own: all
tasks done is evidence, not proof, so it asks.

## 2. Screen inventory

| Screen | Purpose | Serves | Artboard |
|---|---|---|---|
| Goals | Goal cards with derived progress and their projects | §23, §24 | `Goals` |
| Linking | Attaching a task to a project, from the task | §24, §28 | `Linking` |
| States | Five required states, plus the empty goal and the last task | — | `States` |

## 3. Flows

| Flow | Entry | Steps | Exit | Serves |
|---|---|---|---|---|
| Create | Capture | `/add-goal …` or `/add-project …` | Saved | §23, §24 |
| Link | Task detail, "Add to another project" | Search, pick, added | Linked both ways | §24 |
| Complete | Any task completing | Slashit asks whether the goal is achieved | User decides | §23 |

## 4. States

### Goals

| State | What the user sees | Copy |
|---|---|---|
| Empty | Centered serif line and a command to try | "No goals yet" |
| **Empty goal** | Ring reads a dash, not 0%. Dashed box invites the first project | "No projects or tasks yet" / "Add the first project" |
| Loading | Two goal-card skeletons at real height | — |
| Error | Red note | "Goals could not be loaded." |
| Success | Ring, counts, project rows with progress bars | — |
| **Last task done** | Green note asking, with the goal unchanged until answered | "Every task under **Run a half marathon** is done. Mark the goal achieved?" |
| No permission | Not reachable. Per-account behind sign-in | — |

## 5. Responsive behaviour

| Breakpoint | Layout change |
|---|---|
| Mobile (390px) | Goal card keeps the ring but moves counts under the title. Project rows drop the progress bar and keep "3 of 4" |
| Tablet | No distinct layout |
| Desktop | One 780px column |

## 6. Design system deltas

| Change | Kind | Token or component | Why existing one does not fit |
|---|---|---|---|
| Progress ring | added | component | Conic gradient, green token. Dash state when nothing is measured |
| Progress bar | added | component | Per-project, in the goal card |
| Goal card | added | component | Header plus nested project rows. **The first component that contains other records** |
| Link picker | added | component | Search over projects and goals, with an already-linked state |
| Dashed add box | added | component | Invites the first child. 001's empty states are page-level, not inline |
| Achieved pill | changed | `.pill.done` | Same token, new label |

## 6a. Dark theme

Added 2026-09-17, alongside the rest of this design. Dark reuses **001's
approved palette unchanged** — the eighteen token pairs in its `DarkTokens`
artboard, which the shipped `frontend/src/design-system/tokens.css` already
carries byte-for-byte. **This epic adds no colour token**, and it inherits
001's one dark-specific rule: a primary button inverts to a light blue field
with dark ink on it, never white.

Dark artboards on the canvas: `Goals`. States and mobile panels are not
redrawn in dark — they are the same components on the same tokens, and 001
took the same representative-subset approach rather than doubling its canvas.

## 7. Accessibility

| Area | Decision |
|---|---|
| Contrast | Ring and bars use the existing green token. The dash state uses `--ink3` on `--surface`, which passes |
| Keyboard path | Goal cards expand and collapse with Enter. Project rows are links. The link picker is a combobox with a listbox |
| Screen reader labels | The ring is `aria-hidden`; the "5 of 8 tasks done" text beside it carries the value. Progress is never colour-only |
| Motion and reduced motion | The ring does not animate on load |
| Focus order | After linking, focus returns to the task's Part-of list, on the row just added |

## 8. Copy

| Location | Text | Notes |
|---|---|---|
| Progress rule | "Progress counts tasks that are done. A goal with no tasks under it shows no percentage rather than 0%, because nothing has been measured yet." | Explains the dash once, in place |
| Multi-parent | "A task can sit under more than one project. Progress counts it in each." | Names the double-count before it surprises someone |
| Last task done | "Every task under Run a half marathon is done. Mark the goal achieved?" | Asks, never asserts |
| Achieve actions | "Not yet" / "Mark achieved" | |

## 9. Open questions

| # | Question | Owner | Answer |
|---|---|---|---|
| Q1 | Can a task belong to several projects? Drawn yes, which makes progress double-count. Simpler is one parent — but §24 does not say | user, at epic | Open |
| Q2 | Can a project exist without a goal? Drawn as possible; the hierarchy is then two levels, not three | user, at epic | Open |
| Q3 | Is progress only task counts, or weighted? Drawn as a plain count | user, at PRD | Open |
| Q4 | This epic depends on 005 for relationships. If 005 slips, does 008 build its own linking and duplicate it? | user, at epic | Open |
| Q5 | Does a goal have a target date? §23 does not say; nothing is drawn | user, at PRD | Open |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-17 | Created, ahead of the epic and PRD gates | User asked for designs of all upcoming slices, to review later | pending |
| 2026-09-17 | Dark theme added (§6a), reusing 001's approved palette unchanged | User asked for dark designs alongside the light ones | pending |
