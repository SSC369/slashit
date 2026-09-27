---
doc: epic
feature: 004-persistent-memory
title: Persistent Memory
stage: 0
status: approved
owner: user
created: 2026-09-24
updated: 2026-09-25
approved_on: 2026-09-25
supersedes: null
---

# Epic — Persistent Memory

> **Approved** by @user on 2026-09-25. Locked — changes require a change record (§7).

Context: [Product](../product/product.md) · [V1 features](../product/v1-features.md)

Over the 150-line budget by about forty lines: ten questions, the forget
exception and conflict handling each need rows, and none repeats another.

## As supplied

> Whats the next feature we need to implement. Recently we have dome 003 but
> need to do testing. But lets proceed with 004 feat

The requirement itself is the V1 product definition, §15 to §18 and the memory
card in §19, cited rather than copied:
[intake](../product/intake/2026-09-08-personal-jarvis-v1.md#15-memory-records).
`v1-features.md` §3 scopes this epic to exactly those sections. Epic 003 is
built and awaiting its live verification passes; 004 does not depend on it.

## Problem

Slashit can record what the user has to do. It cannot yet record what the user
knows. The facts people most often lose are the ones that are not tasks: a
passport's expiry year, a parent's birthday, a preferred airline, which
subscription renews when. Today these live in a notes app, a chat with oneself,
or nowhere. The source calls memory "one of the core differentiators"
(§16), and product job J2, "What do I need to remember?", has nothing serving it.

Pillar P3, "context accumulates and pays back", is also unserved. Every record
so far is an action with an end state. Nothing Slashit holds is durable context
about the user, so there is nothing for search (005) or proactive help (011) to
draw on later.

## What this feature is

A new record type, the memory: one fact, in the user's own words, that Slashit
keeps until the user tells it to forget. The user saves one with `/remember` or
`/add-memory`, sees every memory in a Memories view under Records, opens any one
to see its category, when it was saved and where it came from, and can edit it
or forget it. `/memories` lists them in the Command Center. `/forget` removes one,
after confirming which. It is the second record type on 001's foundation, after
tasks.

## Requirements in detail

| Area | What it has to do | Why it matters | Notes |
|---|---|---|---|
| Save | `/remember <fact>` and `/add-memory <fact>` both create a memory. The user's wording is kept as the memory's text | Source §16 names both. `/add-memory` is what `/add` filters to in §9 | Both ship as synonyms, per Q1 |
| Category | Each memory carries one category, assigned by Slashit on save and editable afterwards | Source §15 and §19 show a category on every memory | A fixed four: Personal, People, Professional, Life, per Q2 |
| No required fields beyond the fact | A non-empty argument always creates a memory, without a follow-up question | 001's confirmation model asks only when a required field is missing. A fact has one field | So category must never block creation. A failed classification saves the memory uncategorised. The one thing that can pause a save is a conflict, below |
| Memories view | A Memories filter in Records lists every memory with its text, category and save date | Principle 1: "if Slashit can record it, the user can see it". Source §11 and §15 | Rides on 001's records view. Filter by category is likely, sort by date is inherited |
| Memory detail | Shows the text, category, created time and origin, with Edit and Forget | Source §19 draws this card exactly | "Forget", not "Delete", is the source's label |
| Edit | The user edits text and category from the detail | Source §18 | Editing text does not re-run classification unless asked. See Risks |
| `/memories` | Lists memories in the Command Center, most recent first. `/memories <text>` lists only those matching the text | Source §17, §18 | Per Q3 |
| `/memory` | Not shipped | Undefined in the source beyond being listed in §8.2 and §18 | Dropped as a near-duplicate of `/memories`, per Q3 |
| Retrieval | "What do you remember about my career?" returns the memories whose words match | Source §17. This is what makes memory more than a list | Keyword match over memories only, per Q4. A written answer built from memories, as in §17's example, is 005's |
| `/forget <which>` | Finds the memory the argument describes, names it, and asks for confirmation before removing it | Source §18, §35. Principle 3: destructive actions confirm | No match says so. Several matches are listed for the user to pick one, then confirmed, per Q5. This looks simple and is not: it needs a match step before the confirm step |
| Forget everything | `/forget all my memories` states the count and requires explicit confirmation | Source §35 uses this exact example. 001's FR-21 already covers bulk confirms | |
| What forget means | A forgotten memory is gone, not hidden | Pillar P4 rules out "unforgettable memory". 001 soft-deletes records for its audit trail | Per Q6: forget hard-deletes the memory and scrubs its `/remember` line from capture history (001 FR-44). This is a deliberate exception to 001's soft delete and keep-forever history, for memories only |
| Origin | Every memory stores its origin and creation time | Principle 5. Source §19 shows "Source: Jarvis conversation" | Always "command" in V1, since conversation is out |
| Isolation | Memories are read only by their owner, and only the owner's memories reach a prompt | Principle 7 | Memories hold the most sensitive data in the product: documents, family, finances |
| Secret warning | Text that looks like a secret, such as a full card or ID number or a password, saves with a one-line caution | The user stays in control, and gets a nudge before the most sensitive data reaches a model | Warns, never blocks, per Q8 |
| Conflicts | On save, Slashit checks the new memory against the user's existing memories. If it contradicts one or more, nothing is saved yet: Slashit shows the new and the existing memories side by side and asks the user which is correct | Two memories that disagree make retrieval return the stale one. Resolving it silently, as mem0 does, breaks P4, so the user decides | Per Q9, revised 2026-09-25. Three choices, per Q10: keep the new one, which forgets the old, hard-deleted per Q6; keep the old one, which discards the new; or both are correct, which keeps both. Checked on save only, never on edit. This looks simple and is not: detecting a contradiction is a model judgement, and it will sometimes be wrong both ways |
| Conflict question | The question does not block: the user can leave it, run other commands and answer later, as with 001's pending question (FR-36, FR-37). Unanswered, nothing is saved | Reuses a pattern the user already knows rather than inventing a second | |

## Pros

- Serves job J2, which nothing serves today, and pillar P3, which is the
  product's stated reason to exist over a notes app.
- Proves 001's foundation a second time with a record type shaped differently
  from a task: no due date, no status, a category instead. A foundation that
  only fits tasks is found out here, cheaply, before five more types land.
- Small on the capture side. A memory needs no date resolution and no follow-up
  question, so extraction is one field and a category.
- Gives 005 (search) something worth searching, and 011 (proactive) something
  worth surfacing. Both list 004 as a dependency.
- Makes pillar P4 concrete. Forget is the first user-facing action whose whole
  promise is that data leaves.

## Cons

- The data is the most sensitive in the product. Passport numbers, family
  names, health notes. A leak, a prompt crossing users, or a forget that does
  not really forget costs more here than anywhere else.
- Forget collides with decisions already built. 001 soft-deletes and keeps
  capture history forever. Honouring "gone means gone" reopens one or both.
- Retrieval pulls toward 005. Any version of "what do you remember about X"
  that is good enough to be useful is most of personal search, done for one
  record type. Doing it twice is waste; doing it in 005 leaves 004 as a list.
- `/forget <which>` is the first command that acts on an existing record by
  description. 001 deliberately kept edit and delete out of commands (FR-24).
  Memory breaks that rule because the source demands it, and the matching is
  new, fallible machinery.
- Conflict checking is fallible. It will miss some contradictions and flag
  some pairs that are both true, such as two different friends' birthdays. A
  false flag costs the user a question they did not need.
- Every save is now a model call for the category and a comparison against
  existing memories, adding cost and latency on a free product. The comparison
  grows with the number of memories the user holds.

## Best practices and prior art

| Product | How they do it | What to take | What to avoid |
|---|---|---|---|
| ChatGPT Memory | Saves facts from conversation automatically or on request, shows "Memory updated", lists them in a Manage memories screen where each can be deleted | A visible notice at the moment of saving, and one screen listing everything held | Automatic saving the user did not ask for. OpenAI's own help pages say deleting a chat does not delete memories taken from it, which users found surprising. The same trap sits in our capture history |
| Google Gemini, Saved info | The user explicitly adds facts about themselves in a settings list, and the assistant uses them in answers | Explicit save only, which matches commands-only capture | A settings list is a second-class home. Here memory is a record type in Records |
| Claude, memory | Memory the user can view and edit as a summary, scoped per project | Letting the user read exactly what is held, in plain words | A single edited summary loses the per-fact edit and forget the source asks for |
| mem0, open-source memory layer | Each new fact is compared to existing ones and resolved as add, update, delete or no-op | Comparing each new fact to existing ones at save time, the known answer to contradiction | Silent updates. Here the user makes the call, per Q9 |
| Mem, the notes app | Pitched self-organising notes with automatic tagging | Categories assigned by the product, not the user | It leaned on AI organisation the user could not predict. Keep the category set small and editable |

## Alternatives considered

| Option | What it gives | What it costs | Verdict |
|---|---|---|---|
| Do nothing, let notes (009) hold facts | One fewer record type | J2 unserved, the source's stated differentiator gone, 005 and 011 lose their input | Rejected |
| Memory as a tag on notes | One record type instead of two | Notes are open-ended writing, memories are single facts with categories and forget. Merging blurs both and 009 is later in order | Rejected |
| Store and list only. No retrieval, no `/forget` matching; forget from the detail view | Smallest slice, reuses 001's delete path | Leaves §17 and the `/forget` command undone, so 004 is a list of text | Rejected by Q4 |
| Store, list, forget by command, and keyword retrieval over memories only | Delivers every source section in some form without building search | A second retrieval path 005 later replaces or absorbs | Chosen, Q4 answered 2026-09-25 |
| Full semantic retrieval with answers built from memories | The §17 example response, word for word | Most of 005's work, done early and for one type | Rejected for 004. Belongs in 005 |
| Automatic memory from other captures | Context accumulates without the user asking | Commands-only V1 has no conversation to learn from, and silent saving is what ChatGPT's users objected to | Rejected for V1 |
| Use memories as context in other captures, such as resolving "Mom's birthday" in `/add-task` | Real P3 payback, early | Every capture prompt grows, and principle 7 carries more weight per call | Deferred to 005's contextual intelligence, per Q7 |

## Risks and unknowns

| Risk | Likelihood | Impact | What would tell us early |
|---|---|---|---|
| Forget leaves the fact recoverable in capture history, a soft-deleted row, a backup or a provider's logs | high, as built today | high | A test that forgets a memory and then searches every store for its text |
| `/forget` matches the wrong memory and the user confirms without reading | medium | high | Confirmation text that names the memory in full, and a count of how often a forget is followed by a re-save |
| Categories disagree with the user often enough that they stop trusting the view | medium | low | Share of memories whose category is edited after save |
| Edited text keeps a category that no longer fits | medium | low | Same measure, split by edited and unedited |
| Conflict check flags pairs that are both true, and users learn to click through | medium | medium | Share of conflict questions answered "both are correct" |
| Conflict check misses a contradiction and both memories stand | medium | medium | Duplicate-looking pairs per user after a month |
| Comparing against every existing memory makes saves slow or costly as memories grow | medium over time | medium | Save latency and model cost per save, split by how many memories the user holds |
| Users paste secrets, such as full card or ID numbers, into memory | medium | high | Unknown until real use. Q8's warning is the mitigation |
| The model provider's data terms do not meet the bar for this data | unknown | high | Already open as Q10 in the product doc, and it becomes sharper here |

## Open questions

All nine answered by the user on 2026-09-25, each with the recommended option. Q9 was then revised the same day at the user's request, and Q10 followed from it.

| # | Question | Answer |
|---|---|---|
| ~~Q1~~ | Ship both `/remember` and `/add-memory`, or one? | **Both, as synonyms.** |
| ~~Q2~~ | Which categories? §16 and §15 disagree | **A fixed four from §16: Personal, People, Professional, Life.** Slashit assigns one on save, the user can change it |
| ~~Q3~~ | What do `/memory` and `/memories <text>` do? | **`/memories` lists, `/memories <text>` filters, `/memory` is dropped.** |
| ~~Q4~~ | How much retrieval does 004 do? | **Keyword match over memories only.** Written answers wait for 005 |
| ~~Q5~~ | `/forget <which>` matches several memories | **Show the matches, the user picks one, then confirm it by name.** |
| ~~Q6~~ | What does forget delete? | **Hard delete, and scrub the `/remember` line from capture history.** An exception to 001's soft delete, for memories only |
| ~~Q7~~ | Do memories feed other captures in V1? | **No. Deferred to 005.** |
| ~~Q8~~ | Warn when a memory looks like a secret? | **Warn with one line, still save.** |
| ~~Q9~~ | What happens when a new memory contradicts an old one? | **Revised 2026-09-25: ask the user to choose the correct one.** Was "nothing in V1". See Conflicts in Requirements |
| ~~Q10~~ | Q9 opened this: when flagged memories are in fact both true, can the user keep both? Does the check run on edits too? | **Three choices: keep the new, keep the old, or both are correct. Checked on save only, never on edit.** |

> Assumption: Memory Management, listed separately as P1 in `v1-features.md` §1,
> is the edit, forget and view part of this epic, not a later one. No epic in
> the list owns it otherwise.

## What this is not

- Not automatic memory. Nothing is saved that the user did not save by command.
- Not personal search. Searching across tasks, reminders and memories together
  is 005.
- Not a notes app. Long-form writing is 009.
- Not reminders for dated memories. "Mom's birthday is Oct 12" does not create
  a reminder or an event on its own.
- Not shared memory. One account, one owner, per the product baseline.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-24 | Created | User asked to proceed with 004 | pending |
| 2026-09-25 | Conflicting memories brought into scope: on save, a contradiction pauses the save and asks the user which memory is correct. Q9 revised, Q10 added and answered, cons and risks updated | User asked for conflicts to be planned in this feature | user |
| 2026-09-25 | Q1 to Q9 answered, each with the recommended option. Requirements, alternatives and risks updated to match | User answered the open questions | user |
| 2026-09-25 | Approved | User approved, proceed to PRD | user |
