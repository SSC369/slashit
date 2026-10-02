---
doc: features
title: V1 Features
status: approved
owner: user
created: 2026-09-08
updated: 2026-10-02
---

# V1 Features

What V1 ships, how it breaks into epics, and what waits for later. For what
Slashit is and who it serves, read [the product doc](./product.md).

Source: [the V1 product definition](./intake/2026-09-08-personal-jarvis-v1.md).

> Confirmed by the user on 2026-09-08, including the split of reminders out of
> epic 001. Changes from here follow the change log.

---

## 1. V1 capabilities, by priority

Eleven capability areas, prioritised in the source at §40.

| Priority | Capabilities |
|---|---|
| P0 | Command Center, Command System, Structured Records, Persistent Memory, Tasks, Reminders, Personal Search, Context Awareness |
| P1 | Expenses, Events, Today's View, Upcoming View, Goals, Projects, Notes and Ideas, Memory Management |
| P2 | Proactive Suggestions, Advanced Contextual Intelligence |

---

## 2. Slicing rule

Epics are vertical slices, not layers. Every epic except 000 ends with something
the user can do end to end, because the core principle is that anything Slashit
records, the user can see. An epic that stores records without a way to inspect
them would break that principle on the day it ships.

The consequence: epic 001 carries the foundation and proves it with two record
types. Every epic after it adds record types or capabilities onto a working
loop, which is why they get smaller as the list goes on.

---

## 3. The epics

Each epic gets its own folder under `process-docs/` and runs the six gates
independently.

| # | Epic | Priority | Covers (source §) | Depends on |
|---|---|---|---|---|
| 000 | AI Gateway and Usage | P0, platform | AI API key architecture, supplied 2026-09-09 | — |
| 001 | Capture and Records Foundation | P0 | Command Center §7, Command System §8, Command discovery §9, Structured Records §10 to §13, Record detail §19, Tasks §20, Confirmation model §35, Record creation principle §36 | 000 |
| 002 | Authentication | P0, blocking | Real signup, login and email verification, requested 2026-09-14. Not in the source; V1 shipped so far against a dev-only console workaround | — |
| 003 | Reminders and Notifications | P0 | Reminders §21, recurrence, in-app and email delivery | 001, 002 |
| 004 | Persistent Memory | P0 | Memory §15 to §18 | 001, 002 |
| 005 | Personal Search and Context | P0 | Personal search §27, Contextual intelligence §28 | 001, 002, 004 |
| 006 | Expenses | P1 | Expenses §14, expense summaries | 001, 002 |
| 007 | Events | P1 | Events §22 | 001, 002 |
| 008 | Goals and Projects | P1 | Goals §23, Projects §24, goal-project-task relationships | 001, 002, 005 |
| 009 | Notes | P1 | Notes and Ideas §25 | 001, 002 |
| 010 | Daily Control | P1 | Today's view §29, Upcoming view §30, Home dashboard §32, Navigation §33 | 001, 002, 003, 006, 007, 008 |
| 011 | Proactive Slashit | P2 | Proactive Slashit §31, advanced contextual intelligence | 005, 010 |
| 012 | Production Readiness | P0 | Not in the source. Real email sending through Resend, closing 003's T-3.10; ₹ conversion of foreign-currency expenses, from 006's Q7. Rest of scope argued at its own stage 0 | all shipped epics |

---

## 4. Why 000 comes before 001

Epic 000 was added on 2026-09-09 when the user supplied the AI API key
architecture. It is numbered 000 rather than inserted as 002 because epic 001 is
already approved, and renumbering an approved epic would break every reference
to it.

It has to precede 001 rather than follow it. Epic 001 resolves "tomorrow" inside
`/add-task Finish docs tomorrow`, which is a model call, so 001 cannot ship
without the gateway that makes model calls safely.

**000 is the one epic that does not end in something a user can do.** That
breaks the slicing rule above, deliberately. The alternative was to fold the
gateway into 001's build plan, which would bury a security boundary and a
shared-credential limit inside another epic's architecture section, where
neither would get its own review. A platform epic with its own gate is the
lesser evil. It is verified by 001's first successful capture, not by a screen.

---

## 5. Why 001 is first among the product epics, and this shape

The Command Center, the command system and the records store are the product.
Every other epic is a record type or a view layered on them. Tasks ride along in
001 rather than waiting, because a foundation that has never carried a real
record type is not proven.

**Reminders were split out on 2026-09-08**, at the user's direction. They were
the heavier half of the original 001: scheduling, recurrence, two delivery
channels, retry, and the scheduling and delivery infrastructure underneath.
Pulling them out roughly halves the first epic while leaving both halves usable
on their own, which is the test that matters. 001 without reminders still ships a
working product: capture a task by command, see it in records, edit it, complete
it.

The split was deliberately made on the tasks-versus-reminders line rather than on
foundation-versus-record-types. Splitting the other way would have left 001 with
a command bar and a record store and nothing a person could actually record,
which is a layer, not a slice.

Memory follows because it is the stated differentiator, and search in 004 is only
interesting once there is memory to search.

---

## 6. Sequencing

Epics 006, 007 and 009 are near-identical in shape once 001 exists: a new record
type, its command set, its fields, its list view. They can run in any order, or
in parallel, once the foundation is approved. 010 needs the record types it
displays, so it lands after them.

There is no deadline for V1, confirmed 2026-09-08, so the order is driven by
dependency and by what each epic teaches, not by what fits a date.

---

## 7. Deferred out of V1

Cut by the user on 2026-09-08, recorded here so the epic list does not silently
regrow them.

| Cut | Was part of | Why it goes |
|---|---|---|
| Plain-language capture, §3.3 | 001 | V1 captures through commands only |
| Life Inbox, §26 | 008 | It is capture without choosing a type, which commands-only forbids. It returns with plain language or not at all |
| Task priority and recurrence, §20 | 001 | Cost out of proportion to V1 |

---

## 8. Later versions

Nothing here is planned or committed. This section exists so deferred work has a
home other than somebody's memory. A version gets its own document when it
becomes real, not before.

### First candidates after V1

| Candidate | Why it waits | What would bring it forward |
|---|---|---|
| Plain-language capture | Cut from V1 on 2026-09-08. It is the larger half of pillar P1 | Capture volume disappointing under commands-only. This is the first thing to revisit |
| Life Inbox | Cannot exist while capture is commands-only | Returns with plain-language capture, or not at all |
| Task priority and recurrence | Cost out of proportion to V1 | Users asking for it, or reminders in 002 proving the recurrence machinery is reusable |

### Held back until the product is validated

Every item in the product non-goals list. Email management, banking
integrations, health integrations, smart-home control, autonomous purchasing,
social networking, document management, financial planning, a voice-first
assistant, a third-party integration ecosystem, multi-agent workflows,
autonomous decision-making, and teams with sharing and collaboration.

Pricing is the other post-V1 question. It is open as Q5 in
[the product doc](./product.md#13-open-questions).

---

## 9. Open questions

| # | Question | Blocks | Answer |
|---|---|---|---|
| ~~Q1~~ | Is this the right split, and is 001 the right first epic? | all | **Confirmed 2026-09-08.** |
| ~~Q2~~ | Should reminders be pulled out of 001? | 001 | **Yes, done.** Reminders are epic 003. |
| ~~Q3~~ | What is the V1 build window? | sequencing | **No deadline.** |

---

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-08 | Created | V1 product definition supplied | pending |
| 2026-09-08 | Reminders split into epic 002, later epics renumbered to ten. Epic 007 reduced to Notes. Life Inbox, plain-language capture, task priority and recurrence recorded as deferred. Q1, Q2, Q3 closed. | User confirmed the split and cut scope | user |
| 2026-09-09 | Epic 000, AI Gateway and Usage, added ahead of 001. Recorded as a deliberate exception to the vertical-slice rule. | User supplied the AI API key architecture | user |
| 2026-09-14 | Epic 002, Authentication, inserted after 001. Epics 002 to 010 renumbered to 003 to 011, and 002 added to the `Depends on` column of every epic after it, since none can be used by a real user without it. Not in the original source: 001 shipped so far against a dev-only console workaround. | User asked to plan real signup, login and email verification as the immediate next feature | user |
| 2026-09-09 | Superseded `v1-epic-map.md`. Absorbed the V1 capability priorities from the product brief and added a Later versions section. Epic folders are now direct children of `process-docs/`. | User asked for one V1 features document | user |
| 2026-10-02 | Epic 012, Production Readiness, added to the epic table to match the registry, where it has been planned since 2026-09-26. Opens last. No feature made stale. | Registry and this doc disagreed | user |
