---
doc: product
title: Slashit Product
status: in-review
owner: user
created: 2026-09-08
updated: 2026-09-13
---

# Slashit — Product

The standing product context every feature inherits. Read this before drafting
any epic or PRD. For the technical context, read
[the tech stack](../tech-stack.md). For what V1 actually ships, read
[V1 features](./v1-features.md).

Source: [the V1 product definition](./intake/2026-09-08-personal-jarvis-v1.md),
supplied 2026-09-08. Where this document states something the source does not,
it is marked as an assumption.

---

## 1. What Slashit is

Slashit is a command-first AI personal operating system. The user records tasks,
reminders, expenses, memories, events, goals, projects and notes by typing a
command or speaking plainly, and every one of them becomes a structured record
the user can browse, search, edit and delete. Slashit uses that accumulated
context to answer questions about the user's own life.

**Promise.** Tell Slashit what matters. Slashit remembers it, organizes it, and
helps you act on it.

**Positioning.** Not another AI chatbot. An AI-powered personal command center
that remembers and organizes your life.

---

## 2. Who it is for

| Segment | Who they are | What they are trying to do | Why today is hard |
|---|---|---|---|
| The fragmented individual | One person carrying personal and professional responsibilities, goals, projects, recurring tasks, expenses and important dates | Keep one place for everything in their life and get it back when they need it | Their life is split across notes, calendar, reminders, expense trackers, to-do apps, spreadsheets, email and chat. Every capture starts with "where should I put this?" |
| The system-averse | People who dislike maintaining complex productivity systems | Capture without deciding on a taxonomy first | Existing tools ask for structure up front and decay when the user stops maintaining them |

V1 targets a single individual managing their own life. Teams are not a V1
audience.

---

## 3. Product pillars

Every feature must serve at least one. A feature serving none is a signal to
reconsider it.

| # | Pillar | What it means | What it rules out |
|---|---|---|---|
| P1 | Capture without deciding | The user says the thing in one line and it is recorded. | Mandatory category pickers, rigid CLI syntax, forms as the primary input |
| P2 | Everything recorded is visible | Every item Slashit creates appears as a structured record the user can inspect, search, edit and delete. | An opaque assistant whose memory can only be interrogated by asking it |
| P3 | Context accumulates and pays back | Information given once is used later, across conversations, and connected to related items without the user restating it. | Stateless chat, per-session memory, manual relationship management |
| P4 | The user is in control | View, search, edit, delete and forget are always available. Destructive actions confirm. | Silent retention, unforgettable memory, irreversible bulk actions |

> **P1 is partly deferred in V1.** The user decided on 2026-09-08 that V1
> captures through commands only. Picking `/add-task` is still the user deciding
> the type, so V1 delivers the smaller half of this pillar: one place instead of
> six apps. The larger half, saying a thing and having Slashit work out what it
> is, waits. This is a deliberate cut, not an oversight, and it is the first
> thing to revisit if capture volume disappoints.

---

## 4. Principles

Standing rules for every feature, so each PRD does not restate them.

| # | Principle | Source |
|---|---|---|
| 1 | If Slashit can record it, the user can see it. If the user can see it, they can control it. | Core V1 principle, §44 |
| 2 | AI is the interface for creating and querying. Structured views are the interface for inspecting and managing. Neither is a separate source of truth. | §34 |
| 3 | Minimize confirmation. Create immediately when the input is unambiguous, ask one question when it is not, always confirm destructive actions. | §35 |
| 4 | Proactive behaviour is relevant, limited, actionable and non-intrusive. Quality over frequency. | §31 |
| 5 | Every record carries its origin and creation time, so the user can see why it exists. | §19, §36 |
| 6 | Model cost and latency are product decisions, budgeted per feature. | proposed |
| 7 | User data never crosses a user boundary, in storage or in a prompt. | proposed |
| 8 | One Slashit-held provider credential serves many authenticated users. Users never hold a provider key, and every model call is attributed to one user. | AI API key architecture, 2026-09-09 |

> Assumption: principles 6 and 7 are proposed defaults, not stated in the
> source. Confirm or strike them.

**Deleting records.** Records are soft-deleted: a deleted row stays, marked
with when it was deleted, and every view skips it. This is the user's standing
rule from 2026-09-19. **Memories are the one exception for content**, decided in
epic 004 on 2026-09-25: a forgotten memory's row stays, but its words, category
and meaning vector are erased, so forget means the fact is gone. Hard delete
lost because it breaks the standing rule; keeping the text lost because it
breaks the promise of forget.

Principle 7 has a mechanism, not just an intention. See rule T2 in
[the tech stack](../tech-stack.md#4-standing-technical-rules).

---

## 5. Core user jobs

Slashit answers six questions.

| # | Question | Served by |
|---|---|---|
| J1 | What do I need to do? | Tasks, Reminders |
| J2 | What do I need to remember? | Memory |
| J3 | What is happening? | Events, Upcoming |
| J4 | What am I working toward? | Goals, Projects |
| J5 | What have I recorded? | Records |
| J6 | What do I already know? | Personal search, contextual retrieval |

---

## 6. Core entities

One user owns everything. Entities may relate to each other.

```
User
 ├── Tasks          ├── Memories      ├── Projects
 ├── Reminders      ├── Events        ├── Notes / Ideas
 ├── Expenses       ├── Goals         └── Conversations
```

Known relationships: a task may belong to a project or a goal, a project may
serve a goal. Others emerge per feature.

---

## 7. The core loop

```
Capture (command or chat) → Understand → Record / Remember / Act
        → Structured data → Records (search, edit, review)
        → Context accumulates → Slashit helps → Capture
```

---

## 8. Product non-goals

V1 does not attempt to be a fully autonomous Slashit. Feature PRDs inherit
these.

- Email management
- Banking integrations and automatic financial transactions
- Health integrations
- Smart-home control
- Autonomous purchasing
- Social networking
- Full document management
- Advanced financial planning and budgeting
- Voice-first assistant
- A large third-party integration ecosystem
- Complex multi-agent workflows
- Fully autonomous decision-making
- Teams, sharing and collaboration

These may be revisited once the core product is validated.

---

## 9. Success criteria

V1 exists to test three hypotheses.

| # | Hypothesis | Signal |
|---|---|---|
| H1 | Users will record their life in Slashit | Captures per active user per week |
| H2 | Users will inspect their structured data | Share of weekly actives who open a records view |
| H3 | Persistent context creates recurring value | Retrieval actions per week, and week-four retention |

**No pass or fail numbers are set, by decision on 2026-09-08.** With no users
there is no baseline, so a target would be invented. Every signal is
instrumented from launch and read once usage exists.

The consequence, stated plainly: until numbers are set, these hypotheses cannot
be failed, only observed. Set them before any decision to keep building or stop
depends on the result.

---

## 10. Product baseline

Settled product decisions. Technical choices are not here; they are in
[the tech stack](../tech-stack.md).

| Area | Decision | Settled |
|---|---|---|
| Account model | One account per user. No workspaces, no members, no sharing. | 2026-09-08 |
| Surfaces | Web. V1 ships as a web application. Mobile and desktop are not V1. | 2026-09-08 |
| Notification delivery | In-app notifications and email. No push, no SMS. | 2026-09-08 |
| Capture method | Commands only in V1. Plain-language capture is deferred. | 2026-09-08 |
| Theme | Light and dark, following the device only. No user override | 2026-09-13 |
| Design system | Produced in Claude Design at stage 2 of each feature | 2026-09-08 |
| Build window | No deadline | 2026-09-08 |

> Assumption: "in-app notifications or email" is read as both channels shipping,
> with the user choosing. If you meant one of the two, say which and this
> narrows.

---

## 11. Name and mark

**The product is Slashit.** Settled 2026-09-09, after three rounds and fourteen
candidates. Slash was chosen first and reopened when it turned out to collide.
The candidates stay on the epic 001 design canvas as the record of what was
weighed. The GitHub repository still carries the original name, Jarvis.

**The mark** is the slash itself, set in a rounded ink square. Every record in
this product begins with a slash, so the logo is the first thing the user types
rather than a picture of something else.

**The wordmark** is `slash.it` in IBM Plex Mono, the face the product sets
commands in, with the dot in amber. It is the only coloured element.

### The wordmark is not the name

The name is Slashit. **The logo is never set as one undifferentiated lowercase
word.** Set that way it breaks at the wrong place for a lot of readers. This is
the same failure that produced therapistfinder and whorepresents, and it is a
property of the letters rather than of anybody's intent.

It is not a reason to drop the name. It is a reason to always break the word
visibly, which `slash.it` does. Read the full logo system, its lockups, its
misuse rules and its construction, on the epic 001 design canvas, page "Logo".

---

## 12. Business model

| Question | Answer |
|---|---|
| Pricing shape | Not yet decided, see Q5 |
| Free tier | Not yet decided |
| Metered unit | Not yet decided |
| Marginal cost per user | About 0.01 USD a month for a user capturing 100 times, `estimate`. See [the tech stack](../tech-stack.md#5-cost-envelope) |
| Charging users in V1 | No. Not charging for now. |

Not charging was confirmed 2026-09-08 and still holds. What changed on
2026-09-09 is that V1 now has a marginal cost per user rather than none, because
the model moved to a paid tier. The amount is small enough that it changes
nothing about the decision not to charge. It does mean spend is a number to
watch, and the tech stack makes that an obligation.

Pricing returns once the product is validated.

---

## 13. Open questions

| # | Question | Blocks | Owner |
|---|---|---|---|
| Q5 | Pricing shape and metered unit, once V1 is validated? | post-V1 | user |
| Q6 | Currency and locale: is ₹ the only currency in V1? | PRD | user |
| Q8 | Is offline capture required, and is data export a V1 promise? | PRD, build plan | user |
| Q10 | Do Gemini's paid-tier data-handling terms meet the bar for a product holding passports, finances and family details? Narrowed 2026-09-09 when the tier changed. Better terms are the expectation, but expectation is not reading. | launch | user |

Answered and closed: Q1 surface is web, Q2 notifications are in-app and email,
Q3 one account per user, Q4 and Q11 model provider and quota behaviour, Q7
numeric targets deferred, Q9 no deadline, Q12 not charging in V1, Q13 to Q17
platform questions now settled in the tech stack. Their answers are in section
10, section 12 and [the tech stack](../tech-stack.md).

Technical open questions live in
[the tech stack](../tech-stack.md#6-open) as T-Q1 to T-Q8.

---

## 14. Glossary

One definition per term. Docs use the term, never a synonym. If two docs need
two different meanings for one word, the word is wrong. Rename one. Add a term
the first time a doc needs it. Keep definitions to one or two sentences.

### Product terms

| Term | Definition |
|---|---|
| Command Center | The primary Slashit interface where the user types commands, converses, searches and retrieves. |
| Command | An explicit instruction starting with `/`, followed by natural-language arguments. `/add-task Finish API docs tomorrow`. |
| Command discovery | The list of available commands shown when the user types `/`, filtered as they type further characters. |
| Record | One structured item Slashit has stored for the user: a task, reminder, expense, memory, event, goal, project or note. |
| Record type | The category a record belongs to. The V1 types are task, reminder, expense, memory, event, goal, project, note. |
| Records | The structured view of every record the user owns, browsable, searchable, filterable and editable. |
| Record detail | The view of a single record showing every stored field plus its origin and creation time. |
| Origin | How a record came to exist: a command, a conversation, or the Life Inbox. Stored on every record. |
| Memory | Information the user has asked Slashit to retain as durable context, distinct from a task or a note. |
| Forget | Deleting a memory at the user's instruction. Destructive, so it confirms. |
| Life Inbox | Frictionless capture where the user dumps input without categorising it, and Slashit proposes the record type for review. |
| Classification | Slashit deciding which record type a piece of plain-language input becomes. |
| Extraction | Slashit pulling the structured fields for a record type out of natural-language input. |
| Personal search | Unified search across every record type, so the user need not know which category holds the answer. |
| Contextual intelligence | Slashit understanding relationships between records, such as a task belonging to a project that serves a goal. |
| Proactive suggestion | Information Slashit surfaces without being asked. Relevant, limited, actionable, non-intrusive. |
| Today's view | The user's current situation: today's tasks, events, reminders and anything time-critical. |
| Upcoming view | A forward timeline of obligations and important dates. |
| Confirmation model | The rule for when Slashit acts immediately, asks one question, or requires explicit confirmation. |

### Process terms

| Term | Definition |
|---|---|
| Epic | The stage 0 document. The feature thought through in detail: requirements, pros, cons, best practices, alternatives. Nothing is locked. |
| PRD | The stage 1 document. States the problem, users, requirements and success metrics for a feature. Contains no solution. |
| Build plan | The stage 3 document. Locks high-level architecture and asks the user the direction questions. Also called the HLD. |
| Implementation plan | The stage 4 document. File-level plan, contracts, tasks and tests. Also called the LLD. |
| Gate | The approval a stage needs from the user before the next stage starts. |
| Locked | An approved doc whose decisions cannot change without a change record. |
| Design system delta | A token or component added or changed by a feature's design. |

---

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-25 | Deleting records stated in §4: soft delete everywhere, with memories as the one exception whose content is erased. Stale downstream: none | Epic 004's build plan AD-2 graduated on approval | user |
| 2026-09-13 | Theme baseline corrected: no user override, device setting only. This document said "with a user override," settled 2026-09-09, but that override was proposed as FR-42 during epic 001's design and declined on 2026-09-13 (`001-capture-and-records-foundation/02-design.md` Q13). This document had not been updated to match | Found while reading this document before epic 001's build plan | user |
| 2026-09-08 | Created as skeleton, then filled from the V1 product definition | Process bootstrap, then the user supplied the product | user |
| 2026-09-08 | Surface, notifications, model provider, one account per user settled. Plain-language capture, the Life Inbox, and task priority and recurrence deferred out of V1. Pillar P1 marked partly deferred. Numeric targets deferred. Not charging in V1. No deadline. | User answered the blocking product questions and cut scope | user |
| 2026-09-09 | Name settled as Slashit, with the mark and wordmark | User chose the name after three rounds | user |
| 2026-09-09 | Stack revised, and the model tier moved from free to paid, so marginal cost per user is no longer zero | User asked for a stack fit for real users | user |
| 2026-09-09 | Superseded `product-brief.md`. Absorbed the glossary and the name decision. V1 scope moved to [v1-features.md](./v1-features.md). Every technical row moved to [tech-stack.md](../tech-stack.md). | User asked for one product document, with technology kept out of it | user |
| 2026-09-15 | Theme baseline reversed again: a user-facing light/dark toggle is back in scope, overriding the device setting when set. This reopens 001's design decision at Q13 (`001-capture-and-records-foundation/02-design.md`), settled 2026-09-13 the other way, and the 2026-09-13 entry above that recorded no toggle | User asked for a theme toggle while epic 002 was in dev, after first confirming they meant to leave the no-toggle decision alone, then changed their mind | user |
