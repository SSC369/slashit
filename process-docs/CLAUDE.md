# Claude Rules — Writing Process Docs

These rules govern every document under `process-docs/`. They are binding for
Claude. If a user request conflicts with a rule here, say so in one sentence,
then follow the user's decision.

---

## 1. What this folder is

`process-docs/` is the single source of truth for **why** and **what** we build
in Slashit. Code is the answer; these docs are the question, the shape, and the
agreed plan. Nothing gets built that does not have a trail here.

Context is cumulative. A later doc never restates an earlier one — it links to
it. If a fact changes, it is changed **in the doc that owns it**, and the change
is logged.

Three documents hold standing context that every feature inherits:

| Document | Owns |
|---|---|
| [`product/product.md`](./product/product.md) | Product truth. What Slashit is, who it serves, pillars, principles, non-goals, success criteria, name, business model |
| [`product/v1-features.md`](./product/v1-features.md) | What V1 ships, how it breaks into epics, what is deferred, and what later versions might hold |
| [`tech-stack.md`](./tech-stack.md) | Technical truth. The stack, the reasoning behind each choice, standing technical rules, cost envelope |

**Product documents never name a technology.** No framework, no vendor, no
hosting choice, no stack table. Those live in `tech-stack.md` and nowhere else.
A product document that names FastAPI has to be edited every time infrastructure
changes; one that does not survives a stack change untouched.

---

## 2. The six stages

Every feature moves through the same gates, in order. Each stage produces one
document. A stage cannot start until the previous one is **Approved** by the
user.

| # | Stage | Document | Owner of the decision | Locks |
|---|-------|----------|----------------------|-------|
| 0 | Epic | `00-epic.md` | User approves | Nothing. It is where the argument happens |
| 1 | PRD | `01-prd.md` | User approves | Scope, users, requirements, success criteria |
| 2 | Design | `02-design.md` | User approves after Claude Design work | Screens, flows, states, design-system tokens |
| 3 | Build Plan (HLD) | `03-build-plan.md` | User approves | High-level architecture, boundaries, data model, tech choices |
| 4 | Implementation Plan (LLD) | `04-implementation-plan.md`, split into `04.N-*.md` when large | User approves | File-level plan, contracts, task breakdown, test plan |
| 5 | Dev | `05-dev-log.md` | Claude writes as it builds | Nothing — it records reality |

**Gate rule.** Do not write stage N+1 while stage N is `draft` or `in-review`.
If asked to skip ahead, state the missing approval and ask for it. If the user
explicitly says to proceed anyway, proceed and add a `> Gate skipped:` note at
the top of the doc.

A large stage 4 is the one exception, and only inside itself: once the
implementation plan index is approved, a sub-plan may be built while a later
sub-plan is still being drafted. See stage 4 in §6.

**Lock rule.** When the user approves a doc, set its status to `approved` and
add the approval line. An approved doc is not silently edited. Changes go
through §7 (Change Control).

---

## 3. Folder layout

```
process-docs/
├── CLAUDE.md                    ← these rules
├── README.md                    ← human-readable overview of the process
├── index.md                     ← registry of every feature and its stage
├── tech-stack.md                ← the stack, and why each choice won
├── product/
│   ├── product.md               ← what Slashit is, who it serves, pillars
│   ├── v1-features.md           ← V1 scope, the epic list, later versions
│   └── intake/                  ← product-level requirements as supplied
│       └── YYYY-MM-DD-<slug>.md
├── templates/                   ← copy these, never edit in place
└── NNN-<feature-slug>/          ← one folder per feature, directly here
    ├── 00-epic.md
    ├── 01-prd.md
    ├── 02-design.md
    ├── 03-build-plan.md
    ├── 04-implementation-plan.md    ← index when split
    ├── 04.1-<slice-slug>.md         ← sub-plans, only if split
    ├── 05-dev-log.md
    └── assets/                  ← exports, screenshots, canvas links
```

Feature folders sit directly under `process-docs/`. They are numbered in
creation order, three digits, zero padded. Slugs are lowercase kebab-case and
describe the feature, not the ticket. Copy stage documents from `templates/` and
drop `.template` from the name.

There is no decisions folder. A decision that binds more than one feature is
written into the document that owns the fact: `tech-stack.md` for a technical
choice, `product/product.md` for a product one. Both keep the alternatives and
why they lost, so the reasoning survives without a separate record.

---

## 4. Front matter — required on every doc

Every document starts with this block. No exceptions.

```yaml
---
doc: epic | prd | design | build-plan | implementation-plan | dev-log
feature: 003-workspace-memory
title: Workspace Memory
stage: 1
status: draft | in-review | approved | superseded
owner: user
created: YYYY-MM-DD
updated: YYYY-MM-DD
approved_on: YYYY-MM-DD | null
supersedes: null | <path>
---
```

Update `updated` on every edit. Never backdate.

Directly under the front matter, an approved doc carries:

```
> **Approved** by @user on YYYY-MM-DD. Locked — changes require a change record (§7).
```

---

## 5. How to write

**Write for the person who joins in three months.** They have the domain
knowledge and none of the conversation.

- Lead with the decision or the answer. Reasoning goes underneath it.
- One idea per sentence. Around twenty words. Every sentence has a verb.
- Say a thing once. If two sections would carry the same fact, one of them links
  to the other.
- Cut any sentence that survives being deleted. Restating the problem, easing
  into a section, or summarising what the reader just read are all cuts.
- No section preamble. A heading is followed by content, not by a sentence
  explaining what the section is about.
- Justify a decision in one or two sentences. Reasoning that runs longer than
  the decision it supports belongs in the epic, or nowhere.
- Prefer a table or a list to a paragraph for anything parallel: requirements,
  states, options, tasks, risks.
- No em-dashes, no arrows, no parenthetical asides stacked mid-sentence.
- Numbers, limits and measurements live in a table or on their own line, never
  buried in prose.
- Name a file, function or flag only where the reader must go there. Commands,
  schemas and snippets go in fenced code blocks.
- Never invent a fact. If something is unknown, it goes in **Open Questions**
  with a name against it.
- Never mark something done that is not done. Never soften a risk.

**Banned in these docs:** vague scope words with no owner (`robust`,
`seamless`, `enterprise-grade`), features described only as adjectives, and any
requirement that cannot be tested.

**Requirement style.** Every functional requirement is numbered `FR-n`, states
one behaviour, and is verifiable. Non-functional requirements are `NFR-n` and
carry a number.

Bad: `The assistant should respond quickly.`
Good: `NFR-3. Assistant streams the first token within 800 ms at p95.`

**Length.** A document is judged on whether it is complete and reviewable, not on
how much of it there is. A reviewer who stops reading half way has not approved
anything. These are budgets, not limits: go over when the feature genuinely needs
it, and say why in the doc.

| Document | Budget |
|---|---|
| `00-epic.md` | 150 lines |
| `01-prd.md` | 150 lines |
| `02-design.md` | 200 lines |
| `03-build-plan.md` | 250 lines |
| `04-implementation-plan.md`, whole or index | 250 lines. Past 500 it splits, see §6 |
| `04.N-*.md` sub-plan | 250 lines |
| `05-dev-log.md` | no budget. It grows as the work does |
| `product/product.md`, `product/v1-features.md`, `tech-stack.md` | 350 lines |

Over budget, the fix is almost never a smaller feature. It is removing repeated
context, collapsing prose into a table, or moving reasoning to the stage that
owns it. Padding a document to look thorough is a defect, the same as leaving a
required section out.

---

## 6. What each document must contain

Use the matching file in `templates/`. Sections marked required must exist even
when the answer is "none".

### 00-epic.md — Epic

The stage where the feature gets argued out. Nothing is locked here, which is
the point: this is the only stage where a bad idea is cheap.

Required: As supplied, Problem, What this feature is, Requirements in detail,
Pros, Cons, Best practices and prior art, Alternatives considered, Risks and
unknowns, Open questions, What this is not.

Rules:
- **Open with "As supplied", quoting the user verbatim.** Never edit the user's
  stated requirement into something cleaner. Record it, then interpret it below.
  Where the user supplied a product-level document covering several epics, it is
  transcribed once into `product/intake/` and cited here rather than copied.
- Requirements are discussed here, not numbered. Numbering happens in the PRD,
  because a number implies a lock.
- **Pros and cons are required and must both be non-empty.** A feature with no
  cons has not been thought about.
- Best practices means how comparable products solve this, and what they learned.
  Name the product. An assertion about prior art without a name is an opinion.
- Alternatives means other shapes this feature could take, including not building
  it. Say what each would cost and what it would give up.
- This is the one stage where unresolved mess is allowed.

### 01-prd.md — PRD
Required: Problem, Users and jobs, Goals, Non-goals, User stories, Functional
requirements (FR-n), Non-functional requirements (NFR-n), Success metrics,
Dependencies, Risks, Open questions, Out of scope.

Rules:
- No solutions. The PRD says what and why, never how.
- No screen names, no component names, no table names, no framework names.
- **Dependencies name capabilities, never vendors.** "An identity provider, so
  records have an owner" is a dependency. "Supabase Auth" is a technology, and it
  belongs in `tech-stack.md`. Cite the tech stack once if the reader needs it.
- Every goal has a metric. Every metric has a number and a source.
- The Non-goals section is mandatory and must not be empty.
- Requirements here come from the approved epic. A requirement that appears in
  the PRD without having been argued in the epic is a gate skipped.

### 02-design.md — Design
Required: Design intent, Screen inventory, Flows, States per screen (empty,
loading, error, success, permission-denied), Responsive behaviour, Design
system deltas, Accessibility notes, Copy, Open questions.

Rules:
- Every screen maps to at least one FR from the PRD. Cite the FR ids.
- Every interactive surface lists its five states. Missing states are the most
  common defect in this stage.
- Design system changes are listed as deltas: token added, token changed,
  component added. New one-off styles are a smell, call them out.
- Link the Claude Design canvas and store exports in `assets/`.
- The design is fixed when approved. Later code must match it or raise a change
  record.

### 03-build-plan.md — HLD
Required: Architecture summary, Component map, Data model, API surface,
Third-party and model choices, Cross-cutting concerns (auth, tenancy, limits,
cost, observability), Alternatives considered, Architecture decisions,
Questions for the user, Risks.

Rules:
- This document exists to **ask**, not only to state. It must contain a
  `Questions for the user` section covering direction, trade-offs, and anything
  with more than one defensible answer. Ask before choosing, when the choice is
  expensive to reverse.
- Read [`tech-stack.md`](./tech-stack.md) first. The stack is already chosen, and
  its standing technical rules T1 to T8 bind this document. A build plan that
  contradicts one of them says so explicitly and argues for it.
- Every significant choice lists at least one alternative and why it lost.
- For anything calling a model: name the model, the token budget, the fallback
  and the cost per call. Guessed numbers are labelled `estimate`.
- Multi-tenancy, authorisation and data isolation are addressed explicitly on
  every feature that touches user data. "Same as the rest of the app" is not an
  answer; state the rule.
- HLD is locked on approval. A locked decision that affects more than this
  feature is copied into `tech-stack.md` or `product/product.md`, whichever owns
  that kind of fact, in the same commit.
- **A new or changed table is named at the top of the document, not only in
  Data model.** Right after the intro, before section 1: one line per table,
  its name and whether it is new or changed. A reviewer scanning several docs
  sees what touches storage without reading to section 3.

### 04-implementation-plan.md — LLD
Required: Scope recap, File-by-file plan, Interfaces and contracts, Data
migrations, State management, Error handling, Test plan, Rollout and flags,
Task breakdown, Definition of done.

Rules:
- List concrete paths. Say created, modified or deleted for each.
- Type signatures and schemas for anything crossing a boundary.
- Tasks are ordered, independently shippable where possible, and each carries a
  size (S, M, L) and its acceptance check.
- The test plan names the cases, not the intent. `covers FR-4: retry on 429` is
  a case. `good coverage` is not.
- No code is written before this document is approved.
- **A new or changed table is named at the top of the document**, same
  placement and reason as the build plan's rule above, not only in Data and
  migrations. A split sub-plan with its own migration does the same, right
  after its own intro.

**Splitting a large implementation plan.**

One implementation plan that covers everything is unreviewable past a certain
size, and a plan nobody finishes reading is not a plan. When a feature is big,
split it.

Split when any of these is true:

| Trigger | Threshold |
|---|---|
| Tasks in the breakdown | more than 15 |
| Files created or modified | more than 25 |
| Independently shippable slices | more than one |
| Distinct boundaries touched | more than two, for example data, capture pipeline, and the records surface |
| Length of the drafted plan | more than 500 lines |

How it is split:

- `04-implementation-plan.md` stays, and becomes the **index**. Its path never
  changes, split or not, so links and habits hold.
- Sub-plans are siblings, numbered `04.1-<slug>.md`, `04.2-<slug>.md`, in build
  order.
- **Split by vertical slice, never by layer.** A sub-plan ends with something
  that works end to end. `04.1-task-capture` is a slice. `04.1-database-layer`
  is a layer, and it is wrong: nothing can be verified until the last one lands.
- The index holds what is shared and what would otherwise be repeated: scope
  recap, the slice list with dependencies and order, interfaces and contracts
  crossing slice boundaries, data migrations, rollout, and the feature's
  definition of done. Sub-plans link to it, never restate it.
- Each sub-plan holds its own file-by-file plan, its internal contracts, its
  error handling, its test plan, its task breakdown, and its own definition of
  done. It must be buildable from itself plus the index, with nothing else open.
- Task ids carry the sub-plan: task 3 of `04.2` is `T-2.3`. The dev log uses
  these ids and names the sub-plan on every row.
- One dev log per feature, not one per sub-plan.

Approval when split, and this is the point of splitting:

1. The **index is approved first**. That gate locks the slicing, the order, and
   the contracts between slices. Nothing else can be approved before it.
2. Each **sub-plan is approved on its own**, before its own dev starts.
3. Dev on an approved slice may start while a later sub-plan is still being
   written. This is the only place in the process where a stage runs
   concurrently with itself.
4. Changing a contract in the index re-opens every sub-plan that depends on it.
   Say which ones, in the index change log.

Do not split to look thorough. Under the thresholds, one document is better.

### 05-dev-log.md — Dev
Appended during and after implementation. Records what actually happened: what
shipped, what deviated from the plan and why, what was deferred, what broke.
Deviation from an approved plan is always logged, never hidden.

---

## 7. Change control

An approved doc is a contract. To change it:

1. Add an entry to the doc's `Change Log` table at the bottom: date, what
   changed, why, who approved.
2. If the change alters scope, architecture or a locked design, say plainly
   which downstream docs are now stale and list them.
3. Re-run the gate. An epic change re-opens the PRD, design, build plan and
   implementation plan for review, in that order. A PRD change re-opens the
   three below it. Do not carry on building against a stale plan.
4. If a doc is replaced wholesale, set the old one to `superseded` and point
   `supersedes` on the new one at it. Never delete an approved doc.

Standing documents change the same way. `tech-stack.md`, `product/product.md`
and `product/v1-features.md` each carry a change log, and a change to any of
them names the features it makes stale.

---

## 8. Working rules for Claude

1. **Ask before you draft, once.** Read [`product/product.md`](./product/product.md)
   and, before a build plan, [`tech-stack.md`](./tech-stack.md). List the
   questions you actually need answered, at most a handful, grouped. Then draft.
   Do not interview the user one question at a time.
   **Every question or uncertainty put to the user is multiple choice.** List
   every defensible option, each with a one-line consequence. Put your
   recommendation first, marked `(Recommended)`, and leave room for the user's
   own answer. An open-ended question with no options is a defect. The same
   holds for an Open Questions row in any document: it names the options and
   the recommended one, so the user can answer by picking.
2. **Never advance a gate on your own.** Approval is a user action, in words.
   Silence is not approval. "Looks good" is approval; record it with the date.
3. **State assumptions inline.** Any gap you filled yourself is marked
   `> Assumption:` in place, so the user can strike it during review.
4. **Keep the registry current.** Every stage change updates
   [`index.md`](./index.md) in the same commit.
5. **One doc per commit where practical.** Commit message:
   `docs(<feature-slug>): <stage> <verb>`, for example
   `docs(workspace-memory): prd approved`.
6. **Link, do not duplicate.** Reference `01-prd.md#fr-4`, do not restate FR-4.
7. **Cite the source of every number.** Benchmark, vendor page, measurement, or
   `estimate`.
8. **Product-wide learnings graduate.** Anything true beyond one feature moves
   into `product/product.md` if it is product truth, or `tech-stack.md` if it is
   technical. Keep the alternatives and why they lost when it moves.
9. **Keep technology out of product documents.** No framework, vendor or hosting
   name in `product/`, in an epic, or in a PRD. This is rule 1 of §1 and it is
   the one most likely to erode.
10. **Do not write code during stages 0 to 4.** Sketches inside the doc are
    fine. Files in the repo are not.
11. **Report honestly.** If a plan cannot be delivered as approved, say it in
    the dev log the day it becomes true.

---

## 9. Definition of ready and done

**A doc is ready for review when:** front matter is complete, every required
section exists, no `TBD` remains outside Open Questions, every claim is sourced,
it links correctly to the previous stage, and it is inside its length budget in
§5 or says in one line why it is not.

**A feature is done when:** the dev log records every task in the
implementation plan, and in every sub-plan when it was split, as shipped or
explicitly dropped, deviations are logged, the design matches what was approved
or a change record explains why not, and `index.md` shows the feature as
`shipped`.
