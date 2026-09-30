---
doc: prd
feature: 005-personal-search-and-context
title: Personal Search and Context
stage: 1
status: approved
owner: user
created: 2026-09-30
updated: 2026-09-30
approved_on: 2026-09-30
supersedes: null
---

# Epic PRD — Personal Search and Context

> **Approved** by @user on 2026-09-30. Locked — changes require a change record (§7).

Context: [Epic](./00-epic.md) · [Product](../product/product.md) ·
[001 PRD](../001-capture-and-records-foundation/01-prd.md) ·
[004 PRD](../004-persistent-memory/01-prd.md)

Over the 150-line budget by about fifty lines: search, the written answer,
the records view change and related records each carry behaviours that
cannot be merged.

## 1. Problem

Getting a record back from Slashit means knowing its type. `/tasks`,
`/reminders` and `/memories` each look in one place, and the records view
matches only the exact letters typed, so "career" never finds "Become a
backend engineer". Job J6, "What do I already know?", goes unserved, and
hypothesis H3 has almost no retrieval to measure. Every record also stands
alone, so nothing Slashit holds is connected to anything else.

## 2. Users and jobs

| User | Job to be done | Today's workaround |
|---|---|---|
| The fragmented individual | Find a thing without remembering whether it was a task, a reminder or a memory | Run `/tasks`, `/reminders` and `/memories` in turn, or scroll the records view |
| The same user, asking | Get a short answer to a question about their own life, and see where it came from | Read the records and work it out |
| The same user, browsing | See what else Slashit holds that relates to the record in front of them | None |

## 3. Goals

| # | Goal | What we measure |
|---|---|---|
| G1 | Users look things up across types | Searches per active user per week |
| G2 | Searches find what the user wanted | Share of searches where a result is opened |
| G3 | Written answers are trusted | Share of answers where a cited record is opened |
| G4 | Related records are useful | Opens from a related list per record detail view |

> No numeric targets, following the product decision of 2026-09-08
> (`product.md` §9). Every goal is instrumented from launch.

## 4. Non-goals

- Explicit links between records. Linking a task to a project or goal is 008.
- Proactive surfacing. Nothing appears unless the user searches or opens a
  record. That is 011.
- Memories as context for other commands (epic Q4).
- Follow-up questions or a chat thread. One question, one answer.
- Searching capture history (epic Q7).
- Changing `/tasks`, `/reminders` or `/memories`.

## 5. User stories

- **US-1.** As a user, I type `/search passport` and see the memory, the task
  and the reminder that mention it, so that I need not know where I put it.
- **US-2.** As a user, I type `/search career` and find "Become a backend
  engineer", so that my words need not match the record's words.
- **US-3.** As a user, I type `/search when does my passport expire?` and get
  a one-line answer that links to the memory it came from, so that I can
  trust it and correct the record if it is wrong.
- **US-4.** As a user, I search in the records view and get the same records
  `/search` would give me, so that the two never disagree.
- **US-5.** As a user, I open a record and see a few related records, so that
  connections appear without me making them.

## 6. Functional requirements

### Search

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-1 | `/search <text>` searches every record the user owns. It appears in command discovery (001 FR-2) | must | US-1 |
| FR-2 | `/search` with no argument asks what to search for, following 001's FR-8 | must | US-1 |
| FR-3 | Input over 500 characters is refused with the limit stated, and the typed text is preserved | must | US-1 |
| FR-4 | A record matches when it contains a searched word, in any plural or tense form, ignoring common words as 004's FR-20 does | must | US-1 |
| FR-5 | A record also matches when it is close in meaning to the input, with no shared word | must | US-2 |
| FR-6 | A record containing every searched word ranks above any record matched by meaning alone | must | US-1 |
| FR-7 | Results are grouped by record type. Groups are ordered by their best match. Each group shows at most five records, best first | must | US-1 |
| FR-8 | A group with more than five matches states the total and links to the records view, filtered to that type and this search | must | US-1 |
| FR-9 | Each result shows type, title, date and status as in 001's FR-14, and opens its record detail | must | US-1 |
| FR-10 | With no match, Slashit says so and links to the records view | must | US-1 |
| FR-11 | Search covers tasks, reminders and memories. Every record type added later is searchable from the day it ships | must | US-1 |
| FR-12 | Deleted records and forgotten memories never appear in results, answers or related lists | must | US-1, US-5 |
| FR-13 | Records created before this feature ships are searchable by meaning on the day it ships | must | US-2 |
| FR-14 | An edited record is found by its new text, and no longer by its old text, within one minute of the edit | must | US-1 |

Done tasks and past reminders are included, marked by their status (Q2).

### Written answer

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-15 | Input is a question when it ends in `?` or starts with one of: what, when, where, who, why, how, which, do, does, did, is, are, am, have, has. Only a question gets a written answer. Answers 001's Q14 | must | US-3 |
| FR-16 | The answer is at most four sentences, shown above the results, and built only from the user's own records | must | US-3 |
| FR-17 | Every sentence in the answer cites at least one record. Each citation opens that record's detail, and every cited record also appears in the results | must | US-3 |
| FR-18 | When no record supports an answer, Slashit says so in one sentence and states nothing else. Any results still show | must | US-3 |
| FR-19 | When the model is unavailable or the shared quota is exhausted, results still show, with one line saying the answer is unavailable for now | must | US-3 |
| FR-20 | When meaning matching is unavailable, word matches still show, with one line saying results may be incomplete | must | US-1 |
| FR-21 | Capture history keeps the typed search line. Results and the answer are not kept, and the history entry offers to run the search again (epic Q6) | must | US-3 |

### Records view

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-22 | The records view search matches as FR-4 to FR-6 and covers what FR-11 and FR-12 cover. It never writes an answer. Supersedes 001's FR-16 | must | US-4 |
| FR-23 | A search in the records view lists best match first. The user can still sort by date, per 001's FR-17 | must | US-4 |
| FR-24 | The same input, in the same type filter, returns the same records in `/search` and the records view | must | US-4 |

### Related records

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-25 | A record's detail lists up to five other records close in meaning, of any type, closest first, each opening its detail | must | US-5 |
| FR-26 | Only records passing a closeness bar are listed. A record with none shows "Nothing related yet" | must | US-5 |
| FR-27 | The related list is worked out when the detail opens. It is never stored as a link and cannot be edited | must | US-5 |
| FR-28 | A related list that fails to load says so in one line and never blocks the rest of the detail | must | US-5 |

## 7. Non-functional requirements

| id | Requirement | Number | How it is measured |
|---|---|---|---|
| NFR-1 | Only the searching user's records are matched, shown, or placed in a model prompt | Zero incidents | Authorisation tests on every search, answer and related path |
| NFR-2 | Search input and record text never appear in application logs or analytics events | Zero occurrences | Log and event review, and a test asserting it |
| NFR-3 | A search without a written answer responds promptly | Under 1 s at p95 for a user with 3,000 records | Server timing from submit to response |
| NFR-4 | A search with a written answer responds promptly | Under 8 s at p95 for a user with 3,000 records, matching 001 and 004 | Server timing from submit to response |
| NFR-5 | The related list appears promptly | Under 1 s at p95, without delaying the rest of the detail | Server timing |
| NFR-6 | Exact-word hits rank high | The expected record in the top three for over 95% of word queries | Labelled evaluation set, built before build plan approval |
| NFR-7 | Meaning matches are found | The expected record in the top five for over 80% of queries sharing no word with it | Same set |
| NFR-8 | Answers are grounded | Zero sentences without a citation; over 95% of citations support their sentence | Same set, judged by hand |
| NFR-9 | Related lists are relevant | Over 70% of listed records judged related | Same set, judged by hand |

> Assumption: 3,000 records is `estimate` of a heavy V1 user, 004's 1,000
> memories plus tasks and reminders. NFR-6 to NFR-9's thresholds were set by
> the user on 2026-09-30 (Q1), before any measurement.

## 8. Success metrics

Instrumented from launch, reported weekly, no targets set. See section 3.

| Metric | Instrumented by | What it tells us |
|---|---|---|
| Searches per active user per week, `/search` and records view apart | Search events | Whether search earns a habit (G1, H3) |
| Share of searches with a result opened, and its position | Search and open events | Whether the right thing is found (G2) |
| Share of searches with no result | Search events | Where coverage or matching falls short |
| Share of answers with a cited record opened | Answer and open events | Whether answers are checked and trusted (G3) |
| Share of answers saying no record supports them | Answer events | How often questions outrun what is recorded |
| Opens from a related list per detail view | Detail and open events | Whether related records help (G4) |

Events carry counts, types and positions. Never the search text.

## 9. Dependencies

| Dependency | Type | Owner | Status |
|---|---|---|---|
| Command capture, capture history and the records view | internal | 001 | Built |
| An account that owns every record | internal | 002 | Built |
| Reminders and memories as record types | internal | 003, 004 | Shipped |
| A model boundary with per-user attribution and quota | internal | 000 | Built |
| A change record on 001's PRD marking FR-16 superseded by FR-22 | internal | user | Done 2026-09-30 |
| Model provider data terms fit for this data | vendor | user | Open as product Q10 |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| An answer states something no record supports | medium | high | FR-17, FR-18, NFR-8 |
| Meaning matches bury the obvious exact hit | medium | medium | FR-6, NFR-6 |
| Matching by meaning cannot fit inside 1 s. 004 estimated one meaning step at about 1 s | medium | medium | NFR-3 is tested in the build plan. If it cannot hold, the build plan brings it back as a question |
| A later record type is not added to search | medium | medium | FR-11, and a test that fails when a type exists that search does not cover |
| An answer quotes a record deleted or forgotten moments before | low | high | FR-12, FR-21: answers are never kept |
| Answer cost grows with record count | medium over time | medium | NFR-4 at 3,000 records. The build plan states cost per answer |
| Related lists are noise | medium | low | FR-26's bar, NFR-9, G4's metric |

## 11. Open questions

| # | Question | Blocks | Owner | Answer |
|---|---|---|---|---|
| ~~Q1~~ | Are NFR-6 to NFR-9's quality thresholds right? | build plan | user | **Answered 2026-09-30.** As drafted: 95%, 80%, 95%, 70% |
| ~~Q2~~ | Are done tasks and past reminders searchable? | design | user | **Answered 2026-09-30.** Yes, marked by status |

## 12. Out of scope

- Links between records made by the user. 008.
- Surfacing anything unasked. 011.
- Memories feeding other commands.
- Searching capture history, the web or connected accounts.
- Keeping written answers.
- Changes to `/tasks`, `/reminders` and `/memories`.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-30 | Created. Four questions answered before drafting, all recommended: a word rule decides what is a question, 1 s lookups, 8 s answers, 500-character input | Epic approved, user asked to go on | pending |
| 2026-09-30 | Q1 and Q2 answered, both recommended | User answered the open questions | user |
| 2026-09-30 | Approved | User: "Approved, commit and push" | user |
