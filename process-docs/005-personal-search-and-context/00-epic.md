---
doc: epic
feature: 005-personal-search-and-context
title: Personal Search and Context
stage: 0
status: approved
owner: user
created: 2026-09-30
updated: 2026-09-30
approved_on: 2026-09-30
supersedes: null
---

# Epic — Personal Search and Context

> **Approved** by @user on 2026-09-30. Locked — changes require a change record (§7).

Context: [Product](../product/product.md) · [V1 features](../product/v1-features.md)

Over the 150-line budget by about thirty lines. Two things 004 deferred here
and 001's open Q14 each need rows, and none repeats another.

## As supplied

> Whats the next feat we need to build

> Yeah proceed

The requirement itself is the V1 product definition, §27 and §28, with the
retrieval examples in §17 and §38, cited rather than copied:
[intake](../product/intake/2026-09-08-personal-jarvis-v1.md#27-personal-search).
`v1-features.md` §3 scopes this epic to §27 and §28. Two items were handed
here by earlier epics and must be settled here:

- Epic 004 deferred written answers built from memories, matching by meaning,
  and memories as context in other captures (`004/01-prd.md` §4).
- Epic 001 left Q14 open for this epic: does `/search` answer in sentences, or
  only return matching records (`001/01-prd.md` §11)?

## Problem

Slashit now holds three record types: tasks, reminders and memories. Getting
something back means knowing which type holds it. `/tasks`, `/reminders` and
`/memories` each look in one place. The Records view searches all three, but
only for the exact letters typed: "career" finds nothing filed under "backend
engineer". The source's test, "the user shouldn't need to know which category
contains the information" (§27), fails today.

Job J6, "What do I already know?", has nothing serving it. Hypothesis H3,
that persistent context creates recurring value, is measured by retrieval
actions per week (`product.md` §9). With no way to ask a question across
records, the signal H3 depends on barely exists.

Pillar P3 promises information given once is "connected to related items
without the user restating it". Nothing connects anything yet. Each record
stands alone.

## What this feature is

One command, `/search <anything>`, that looks across every record type the
user owns and returns what matches, by words and by meaning, grouped by type.
When the input reads as a question, such as "What am I working toward?", a
short written answer sits above the records, built only from those records and
citing each one it used. The Records view search uses the same matching, so
the two never disagree. A record's detail shows a few related records, found
by meaning, so connections appear without the user making them.

## Requirements in detail

| Area | What it has to do | Why it matters | Notes |
|---|---|---|---|
| `/search <text>` | Returns matching records across every type, grouped by type, best match first | Source §27 draws exactly this: `/search passport` returns a memory, a task and a reminder | New command. Appears in command discovery (001 FR-2) |
| Types covered | Every record type that exists when 005 ships: tasks, reminders, memories | A search that silently skips a type breaks §27's promise | Later types (006 to 009) join search as each ships, per Q3. Each later epic must carry this as a requirement, or search goes stale |
| Match by words | Exact words, and their plural and tense forms, still match | "passport" must find "Renew passport" every time. Meaning-only search sometimes ranks the obvious hit below a near miss | 004 already stems words for `/memories` |
| Match by meaning | "career" finds "Become a backend engineer" | Source §17's example has no shared word between question and answer | Per Q2, words and meaning combined. This looks simple and is not: it needs every existing task and reminder made searchable by meaning, not only new ones |
| Written answer | A question gets two to four sentences above the records, as in §17 and §38 | This is what makes search more than a filter. 004 deferred it here | Per Q1. Built only from the user's own records. See Grounding |
| Grounding | Every statement in the answer cites the record it came from, and each citation opens that record | Principle 2: the AI is not a separate source of truth. A statement the user cannot trace is one they cannot correct | If no record supports an answer, it says so and shows nothing invented. This looks simple and is not: a model will fill gaps unless it is checked |
| Answer unavailable | If the model is down or over its limit, records still return, with a one-line note that the answer is missing | The records are the product; the sentence is a convenience | Word matching works with no model call |
| No match | Says nothing matched, and names the closest types to browse | Source §35: minimize dead ends | |
| Records view search | Uses the same matching as `/search`, results only, no written answer | Principle 2. Two searches that return different records for one query teach the user neither is reliable | Per Q5. Replaces 001 FR-16's letter matching |
| Related records | A record's detail lists up to five other records close in meaning, any type, each opening its detail | Source §28 and pillar P3: "the user doesn't need to manually explain these relationships" | Per Q4. Read-only, computed, never stored as a link. Explicit goal, project and task links are 008's |
| Memories in other captures | Per Q4, not in V1 | 004 handed this here to decide | Using memories to fill a capture changes what a command does based on hidden context, which works against principle 3's "create immediately when unambiguous" |
| Deleted and forgotten | A soft-deleted record never appears in results, answers or related lists. A forgotten memory cannot, because it no longer exists | Principle 7 and 004's forget promise | A cached answer that quotes a since-forgotten memory would break 004's NFR-2. Answers are not stored, per Q6 |
| Isolation | Only the searching user's records are matched, sent to a model, or shown | Principle 7 | The written answer is the first prompt that carries many records of mixed types at once |
| Origin | A search creates no record. It appears in capture history like `/memories` does | Principle 5 applies to records; a search is a read | |

> Assumption: `/search` is the only new command. Source §17 shows
> `/search What do you remember about my career?` handled by search, so
> `/memories <text>` stays keyword-only over memories, as 004 shipped it.

## Pros

- Serves job J6, which nothing serves, and gives H3 its retrieval signal.
- Pays back 004. Memories become useful the moment they can be found by
  meaning and summarized, not only listed.
- Closes 001's Q14 and three items 004 deferred, so no epic keeps an open
  hand-off.
- Small on the record side. No new record type, no new capture path.
- Unblocks 008 and 011, which both list 005 as a dependency.
- Related records make P3 visible with no work from the user.

## Cons

- The written answer is the first place Slashit states things about the user
  in its own words. A wrong sentence costs more trust than a missing one.
- Meaning search on every existing task and reminder is a one-off backfill,
  and a cost on every later save of every type.
- Cost grows with use. Each question is a model call carrying many records,
  far larger than a capture. `product.md` principle 6 makes that a budget to
  set, not ignore.
- Every later epic inherits a duty: its record type must join search. Forget
  it once and search quietly lies by omission.
- "Related" by meaning will sometimes pair things that only share words, such
  as two unrelated tasks both mentioning "Monday".
- Replacing the Records view's letter matching changes shipped behaviour in
  001. A user who typed part of a word and got a hit may now get ranked
  results instead.

## Best practices and prior art

| Product | How they do it | What to take | What to avoid |
|---|---|---|---|
| Apple Spotlight | One box across apps and file types, results grouped by kind, one top hit | Group by type; one best hit first | Treating every type equally when one is plainly the answer |
| Notion AI Q&A | Answers questions across a workspace in prose, with links to the source pages | Cite every source; the answer is a door to the records | Long answers. The user came for a fact |
| Mem | Search by meaning across notes, and a panel of similar notes beside each note | Related items shown in place, not behind a command | Automatic linking the user cannot see the reason for |
| Obsidian | Backlinks pane splits linked mentions from unlinked ones | Keep computed relations apart from links the user made | Making the user maintain links, which the source rules out |
| Google Photos | Search by meaning ("beach") with no tags written by the user | Proof users accept meaning search when the top results are right | Hiding exact-word matches below looser ones |

## Alternatives considered

| Option | What it gives | What it costs | Verdict |
|---|---|---|---|
| Do nothing | No cost. Records view search already spans types | §27 unmet, J6 unserved, H3 unmeasurable. 008 and 011 blocked | Rejected |
| Records only, no written answer | Cheap, fast, never wrong in its own words | Fails §17 and §38's examples; `/search` becomes the Records filter in the Command Center | Rejected, per Q1 |
| Written answer only, no record list | Feels like an assistant | Breaks principle 2: the answer becomes the source of truth | Rejected |
| Stored links between records now | Real relationships, reusable by 008 | Duplicates 008's goal, project and task links before those types exist | Deferred to 008 |
| Memories fill other captures | `/remind call mom on her birthday` could find the date | Hidden context changes outcomes; hard to explain; new failure mode on every capture | Rejected, per Q4 |
| Search conversation history too | Finds things said but never saved | V1 has no conversation outside commands; turns mostly repeat records | Rejected, per Q7 |

## Risks and unknowns

| Risk | Likelihood | Impact | What would tell us early |
|---|---|---|---|
| The answer states something no record supports | medium | high | Share of answer sentences with no valid citation, checked in tests and sampled after launch |
| Meaning matches outrank the obvious exact hit | medium | medium | Share of searches where the user opens a result below the third |
| A later epic's type is not added to search | medium | medium | A test that fails when a record type exists that search does not cover |
| Question calls are costly as records grow | medium over time | medium | Model cost per question, split by the user's record count |
| An answer quotes a record deleted or forgotten between search and display | low | high | A test that forgets a memory during an open search and checks the answer |
| Backfill of existing tasks and reminders fails partway | low | low | Count of records with no meaning data after the backfill |
| Related records are noise and the panel is ignored | medium | low | Opens from the related list per detail view |
| The model provider's data terms do not meet the bar | unknown | high | Already open as Q10 in `product.md`. Sharper here: one prompt now carries many record types |

## Open questions

All eight answered by the user on 2026-09-30, each with the recommended option.
Q6 was re-asked in plainer words first.

| # | Question | Answer |
|---|---|---|
| ~~Q1~~ | Does `/search` write an answer? Closes 001's Q14 | **Only when the input reads as a question.** Keyword searches return records alone |
| ~~Q2~~ | How are records matched? | **Words and meaning combined.** Exact hits stay on top |
| ~~Q3~~ | Which types does search cover? | **Every type at ship time, and each later epic adds its own.** |
| ~~Q4~~ | What does "context" mean in V1? | **Related records on a record's detail, by meaning. Memories do not feed other captures.** |
| ~~Q5~~ | Does the Records view search change? | **Yes, same matching as `/search`, no written answer.** Supersedes 001 FR-16; a change record on `001/01-prd.md` lands with this epic's PRD |
| ~~Q6~~ | Are written answers kept? | **No.** The question stays in capture history; the answer is generated each time and never stored |
| ~~Q7~~ | Does search look at capture history? | **No, records only.** |
| ~~Q8~~ | How many results does `/search` show? | **Up to five per type, with a link to see all in Records.** |

## What this is not

- Not explicit relationships. Linking a task to a project or a goal is 008's.
- Not proactive. Nothing is surfaced unless the user searches or opens a
  record. That is 011.
- Not memory as capture context, per Q4.
- Not a chat. A question gets one answer; there is no follow-up thread,
  because conversation outside commands is out of V1 (001 FR-11 withdrawn).
- Not search of other people's data, the web, or connected accounts.
  Product non-goals exclude integrations.
- Not a change to `/tasks`, `/reminders` or `/memories`. They keep listing one
  type.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-30 | Created | User asked for the next feature and to proceed | pending |
| 2026-09-30 | Q1 to Q8 answered, each with the recommended option. Alternatives updated to match | User answered the open questions | user |
| 2026-09-30 | Approved | User: "Commit and go with next" | user |
