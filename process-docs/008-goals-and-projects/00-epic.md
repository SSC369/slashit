---
doc: epic
feature: 008-goals-and-projects
title: Goals and Projects
stage: 0
status: approved
owner: user
created: 2026-09-30
updated: 2026-09-30
approved_on: 2026-09-30
supersedes: null
---

# Epic — Goals and Projects

> **Approved** by @user on 2026-09-30. Locked — changes require a change record (§7).

Context: [Product](../product/product.md) · [V1 features](../product/v1-features.md)

## As supplied

> Go with epic 008

The requirement is the V1 product definition, §23 Goals and §24 Projects,
cited rather than copied:
[intake](../product/intake/2026-09-08-personal-jarvis-v1.md#23-goals).
`v1-features.md` §3 scopes this epic to those two sections and the
goal-project-task relationships, and makes it depend on 001, 002 and 005.

Four questions were answered before drafting, all as recommended, on
2026-09-30:

| # | Question | Answer |
|---|---|---|
| A1 | Where does progress come from? | A project's is its done tasks over all its tasks. A goal's comes from its linked projects and tasks, with an optional manual percentage for goals no task list measures, such as "Save ₹2 lakh" |
| A2 | Which project does `/add-project-task` add to? | With one project, that one. With several, Slashit asks which, as 001 asks for a missing field. It never guesses |
| A3 | How does an existing task join a goal or project? | Goal and Project pickers on the task's edit form. No new command |
| A4 | Should 005's related records suggest links? | No. Links are only ever made by the user. Suggestions may come with 011 |

## Problem

Slashit records what to do and what to remember, but not why. Job J4, "What am
I working toward?", has nothing serving it. A task like "Finish the Spring Boot
course" sits beside "Buy milk" with nothing saying it serves a goal to become a
backend engineer. The user keeps that structure in their head, or in another
app, which is the fragmentation the product exists to end (`product.md` §2).
Epic 010, Daily Control, depends on this one to show goal progress and focus.

Pillar P3 promises records connected to related items. 005 connects them by
meaning, but those links are guesses and say so ("not links you made"). No
record can yet belong to another on the user's say-so.

## What this feature is

Two new record types and the links between them. A **goal** is a long-term
outcome: "Become a backend engineer". A **project** is a body of work: "Backend
learning". A project may serve one goal, and a task may belong to a project, a
goal, or both.

Commands, from §23 and §24: `/add-goal`, `/goals`, `/update-goal`,
`/add-project`, `/projects`, `/add-project-task`. Each goal and project shows
its progress, computed as A1 says. Goals and Projects get their own tabs in
Records, each record a detail page listing what is linked to it. The task
detail gains Goal and Project pickers (A3).

## Requirements in detail

| Area | What it has to do | Why it matters | Notes |
|---|---|---|---|
| Goal record | Title, status, optional manual progress, created time and origin | P2: every record visible and editable | Active, Achieved or Dropped, Q1 |
| Project record | Title, status, optional goal | The middle layer between intent and tasks | One goal per project, Q2 |
| Task links | At most one project and at most one goal per task | A task under a project that serves a goal already counts toward that goal | Direct goal link covers tasks with no project |
| Progress | Project: done tasks over all live tasks. Goal: over every task linked directly or through its projects, unless a manual value is set | The number the intake shows on every goal | A project with no tasks shows no percentage, not 0% |
| `/add-project-task` | Creates a task inside a project | §24's own example | Target project as A2. Looks simple and is not: a pending question, as in 001 |
| `/update-goal` | Changes a goal's status or manual progress | §23 | A status word or a percentage, no model call, Q4 |
| Records | Goals and Projects tabs; detail pages list linked projects and tasks | H2: users inspect their data | The intake's §6 line: "Backend Learning, 8 Tasks, 35% Complete" |
| Deleting | Soft-delete, as every record but a memory | Standing rule, 2026-09-19 | Linked tasks stay and lose the link, Q3 |
| Search | Goals and projects are searchable, and have related records, from the day they ship | 005's FR-11. 005's coverage test fails the build without a search port per type | Each needs an embedding and a search port, as tasks got in 005 |
| Isolation | A link never points across users | Principle 7 | Checked by the same boundary tests as every record |

## Pros

- Serves J4, the one core job with nothing behind it.
- P3: links the user makes are exact, where 005's meaning links are guesses.
- P2: progress is computed from records the user can see, never asserted.
- Unblocks 010, which needs goals and projects to show.
- The manual progress option covers goals no task list measures, without
  inventing numbers for them.

## Cons

- Two record types at once, each with a full surface: commands, tabs, detail,
  edit, delete, search. It is about the size of 001.
- Links add state that can go stale: a task moved or deleted changes two other
  records' progress.
- Derived progress rewards splitting work into many small tasks. A goal with
  one huge task and one tiny one reads 50% either way.
- `/add-project-task` needs a pending question, the most bug-prone part of 001.
- More commands to learn under commands-only capture, which is already P1's
  weak half.

## Best practices and prior art

| Product | How they do it | What to take | What to avoid |
|---|---|---|---|
| Asana | Goals link to projects; progress updates from them or is set by hand | Both modes, chosen per goal | Goal hierarchies and workspaces: team tooling |
| Linear | Project progress is completed issues over total | Derived progress from the work itself | Estimates and weighting: too much for one person |
| Things 3 | Areas hold projects hold to-dos; a project shows a progress pie | Few levels, progress glanceable in the list | No goals at all: the "why" layer is missing |
| Notion | Relations and rollups the user wires up | Links as plain, visible fields | Building the schema yourself: P1 rules it out |

## Alternatives considered

| Option | What it gives | What it costs | Verdict |
|---|---|---|---|
| Do nothing | No new surface | J4 unserved; 010 has nothing to show | Rejected: J4 is a core job |
| Goals only, projects as tags | Half the build | §24 unmet; tags drift and cannot hold status | Rejected |
| Projects only, goals later | Smaller first step | §23 unmet; the "why" layer is the point | Rejected: one epic, sliced at stage 4, Q5 |
| Nested goals and sub-projects | Mirrors real plans | Deep trees for one person; progress rules multiply | Rejected for V1 |

## Risks and unknowns

| Risk | Likelihood | Impact | What would tell us early |
|---|---|---|---|
| Progress reads wrong and users stop trusting it | medium | high | Goals with manual progress far outnumbering derived ones |
| The pending question in `/add-project-task` loops or misroutes | medium | medium | 001's own pending-question tests, reused |
| Scope matches 001 and slips 010 | medium | medium | The implementation plan passing the split thresholds |
| Search coverage missed for the new types | low | medium | 005's coverage test, which fails the build |

## Open questions

| # | Question | Options | Blocks | Owner |
|---|---|---|---|---|
| ~~Q1~~ | What statuses does a goal have? | (a) Active, Achieved, Dropped (Recommended); (b) Active, Done; (c) no status, progress only. **Answered 2026-09-30.** (a) Active, Achieved, Dropped | PRD | user |
| ~~Q2~~ | How many goals can a project serve? | (a) At most one (Recommended; progress has one home); (b) many. **Answered 2026-09-30.** (a) At most one | PRD | user |
| ~~Q3~~ | Deleting a project or goal: what happens to its linked tasks? | (a) Tasks stay and lose the link (Recommended; nothing is lost); (b) tasks are deleted too, after a confirm naming them; (c) delete is refused while tasks are linked. **Answered 2026-09-30.** (a) Tasks stay and lose the link; the confirm says how many | PRD | user |
| ~~Q4~~ | What does `/update-goal` accept? | (a) A status word or a percentage, "/update-goal Save ₹2 lakh 45%" (Recommended); (b) opens the goal's edit form; (c) free text read by the model. **Answered 2026-09-30.** (a) A status word or a percentage, read without the model | PRD | user |
| ~~Q5~~ | One epic, or split into projects first and goals second? | (a) One epic, split into slices at stage 4 (Recommended; 010 needs both); (b) two epics. **Answered 2026-09-30.** (a) One epic, sliced at stage 4 | PRD | user |

## What this is not

- Not links suggested or made by Slashit (A4).
- Not nested goals, sub-projects, milestones or dependencies between tasks.
- Not sharing a goal or project with anyone: teams are a product non-goal.
- Not time tracking, estimates or weighted progress.
- Not the Today, Upcoming or Home views that show goals: epic 010.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-30 | Created, with A1 to A4 answered first | 005 merged; user asked for 008 | user |
| 2026-09-30 | Q1 to Q4 answered, all as recommended | User answered the open questions | user |
| 2026-09-30 | Q5 answered, one epic. Approved | User: "Approve, commit and push" | user |
