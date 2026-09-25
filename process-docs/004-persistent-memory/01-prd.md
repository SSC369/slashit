---
doc: prd
feature: 004-persistent-memory
title: Persistent Memory
stage: 1
status: approved
owner: user
created: 2026-09-25
updated: 2026-09-25
approved_on: 2026-09-25
supersedes: null
---

# Epic PRD — Persistent Memory

> **Approved** by @user on 2026-09-25. Locked — changes require a change record (§7).

Context: [Epic](./00-epic.md) · [Product](../product/product.md) ·
[001 PRD](../001-capture-and-records-foundation/01-prd.md)

Over the 150-line budget by about fifty lines: forget and conflict handling
each carry several testable behaviours that cannot be merged.

## 1. Problem

Slashit records what the user has to do, but not what the user knows. Facts
such as a passport's expiry, a parent's birthday or a preferred airline have no
home, so job J2, "What do I need to remember?", goes unserved. These are also
the most sensitive facts a person holds, so the user must be able to see every
one and remove any of them for good.

## 2. Users and jobs

| User | Job to be done | Today's workaround |
|---|---|---|
| The fragmented individual | Keep durable personal facts in the same place as their tasks, and get them back by a word | A notes app, a chat with themselves, or memory |
| The same user, later | Correct a fact that has changed without ending up with two versions | Edit or delete by hand, if they remember the old one exists |
| The privacy-conscious user | Remove a fact so that Slashit no longer holds it anywhere they can reach | None. Nothing in Slashit is truly deleted today |

## 3. Goals

| # | Goal | What we measure |
|---|---|---|
| G1 | Users save facts in Slashit | Memories saved per active user per week |
| G2 | Saved facts are returned to | Memory lookups per active user per week, by `/memories` or the Memories filter |
| G3 | Memory stays free of contradictions without silent changes | Conflict questions answered, split by the three answers |
| G4 | Forget is trusted | Forgets followed by any memory save within five minutes. Revised 2026-09-25: a forgotten text is erased, so similarity cannot be measured |

> Assumption: no numeric targets, following the product decision of
> 2026-09-08 (`product.md` §9). Every goal is instrumented from launch.

## 4. Non-goals

- Automatic memory. Nothing is saved that the user did not save by command.
- Written answers built from memories, such as "You told me you want to
  become a backend engineer". That is personal search, epic 005.
- Matching by meaning. "career" finds a memory only if the memory contains
  the word. Related-meaning retrieval is 005.
- Using memories as context in other captures. Deferred to 005.
- Reminders or events created from dated memories.
- Checking edits for conflicts. Only new saves are checked.

## 5. User stories

- **US-1.** As a user, I type `/remember My passport expires in 2030`, so that
  Slashit keeps the fact without me choosing where it goes.
- **US-2.** As a user, I open my memories and see every fact Slashit holds,
  with its category and when I saved it, so that nothing is hidden from me.
- **US-3.** As a user, I type `/memories passport`, so that I get the fact
  back without scrolling.
- **US-4.** As a user, I edit or forget a memory, so that what Slashit holds is
  what I want it to hold.
- **US-5.** As a user, when I save a fact that contradicts one I saved before,
  I am asked which is correct, so that I never hold two versions of the truth.
- **US-6.** As a user, when I forget a memory, it is gone from everything I can
  reach, including my capture history, so that forget means forget.

## 6. Functional requirements

### Save

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-1 | `/remember <fact>` and `/add-memory <fact>` both save a memory, with identical behaviour. Both appear in command discovery | must | US-1 |
| FR-2 | The memory's text is the argument as typed, with surrounding whitespace removed. Slashit never rewrites it | must | US-1 |
| FR-3 | A save with no argument asks one question for the fact, following 001's FR-8 | must | US-1 |
| FR-4 | A fact longer than 500 characters is refused with the limit stated, and the typed text is preserved | must | US-1 |
| FR-5 | Every memory carries one category from a fixed four: Personal, People, Professional, Life. Slashit assigns it on save | must | US-1 |
| FR-6 | When Slashit cannot decide a category, the memory is saved uncategorised. Category never causes a question | must | US-1 |
| FR-7 | After saving, Slashit shows the memory's text and category where the user typed, following 001's FR-7 | must | US-1 |
| FR-8 | A fact that looks like a full payment-card number, a government ID number or a password saves normally, with a one-line caution saying why | should | US-1 |
| FR-9 | When the model is unavailable, the save is refused as in 001's FR-35, and the typed text is preserved. Nothing is saved without a conflict check | must | US-1 |

### Conflicts

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-10 | Every new save is checked against the user's existing memories. When it contradicts one or more, nothing is saved yet, and Slashit shows the new fact beside each contradicting memory and asks which is correct | must | US-5 |
| FR-11 | The question offers three answers. Keep the new: the new memory is saved and the contradicting ones are forgotten, per FR-22. Keep the old: the new fact is discarded. Both are correct: the new memory is saved and all are kept | must | US-5 |
| FR-12 | The "keep the new" answer names every memory it will forget. Choosing it is the confirmation | must | US-5 |
| FR-13 | The question does not block. It stays where it was asked, can be answered later, and saves nothing while unanswered, following 001's FR-36 and FR-37 | must | US-5 |
| FR-14 | Editing a memory never runs the conflict check | must | US-4 |

### View and edit

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-15 | The records view offers a Memories filter listing every memory with its text, category and save date, newest first | must | US-2 |
| FR-16 | Memories can be filtered by category, including uncategorised | should | US-2 |
| FR-17 | Opening a memory shows its text, category, creation time, origin and last edit time, with Edit and Forget actions | must | US-2 |
| FR-18 | The user can edit a memory's text and category. Editing the text leaves the category unchanged. The 500-character limit applies | must | US-4 |
| FR-19 | `/memories` lists the user's memories, newest first | must | US-3 |
| FR-20 | `/memories <text>` lists memories containing at least one of the text's words, ignoring common words such as "what", "about" and "my". Memories containing more of the words come first. No match says so | must | US-3 |

### Forget

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-21 | Forget from the memory detail asks for confirmation, naming the memory's full text | must | US-4 |
| FR-22 | A forgotten memory is removed permanently. It no longer appears in the records view, in `/memories`, in any count, or in any conflict check, and it cannot be restored | must | US-6 |
| FR-23 | Forgetting a memory replaces its words in capture history with "A memory was saved here and later forgotten". This covers the turn that saved it and any conflict question that showed it | must | US-6 |
| FR-24 | `/forget <which>` with exactly one matching memory asks for confirmation, naming its full text | must | US-4 |
| FR-25 | `/forget <which>` with several matching memories lists them, lets the user pick one, then confirms it by name | must | US-4 |
| FR-26 | `/forget <which>` with no match says so and forgets nothing | must | US-4 |
| FR-27 | An instruction to forget every memory states the count and requires explicit confirmation, following 001's FR-21 | must | US-4 |
| FR-28 | A confirmed `/forget` turn keeps only "Forgot 1 memory" or the count in capture history, not the words used to find it | must | US-6 |
| FR-29 | Every forget confirmation says that backup copies are removed within the backup retention window, and states that window | must | US-6 |

> Assumption: FR-28 extends FR-23's promise to the `/forget` line itself,
> because "forget my passport number" can carry the fact. Strike it if the
> forget line should stay as typed.

## 7. Non-functional requirements

| id | Requirement | Number | How it is measured |
|---|---|---|---|
| NFR-1 | A user's memories are never readable by another user, in storage or in a model prompt | Zero incidents | Authorisation tests on every memory path |
| NFR-2 | After a forget, the memory's text is found in no store the product reads | Zero matches | Test that forgets a memory, then searches every store for its text |
| NFR-3 | Memory text never appears in application logs or analytics events | Zero occurrences | Log and event review, and a test asserting it |
| NFR-4 | A save is confirmed, or its conflict question shown, promptly | Under 8 s at p95 for a user with 1,000 memories. Revised 2026-09-25 from 2 s: every save makes one model call, and 001 measured those at 5.3 to 8.5 s (001 dev log, I-1 and I-2) | Server timing from submit to response |
| NFR-5 | `/memories` and the Memories filter respond promptly | Under 1 s at p95 for a user with 1,000 memories | Load test |
| NFR-6 | Categories are right on everyday facts | Over 85% correct | Labelled evaluation set, built before build plan approval |
| NFR-7 | The conflict check catches real contradictions and rarely flags true pairs | Catches over 80%, flags under 10% of non-contradicting pairs | Labelled evaluation set, built before build plan approval |

> NFR-4 was set by the user on 2026-09-25, and NFR-5 to NFR-7 confirmed the
> same day. 1,000 memories is `estimate` of a heavy V1 user.

## 8. Success metrics

Instrumented from launch, reported weekly, no targets set. See section 3.

| Metric | Instrumented by | What it tells us |
|---|---|---|
| Memories saved per active user per week | Save events | Whether memory earns a habit (G1, H1) |
| Memory lookups per active user per week | `/memories` and filter events | Whether facts come back out (G2, H3) |
| Conflict answers by type | Conflict question events | A high "both are correct" share means the check over-flags (G3) |
| Forgets followed by any memory save within five minutes | Forget and save events | Whether `/forget` picks the wrong memory (G4). An upper bound: some re-saves are unrelated |
| Share of memories whose category is edited | Edit events | Whether categories are trusted |
| Saves carrying the secret caution | FR-8 events | How much sensitive data users put in |

## 9. Dependencies

| Dependency | Type | Owner | Status |
|---|---|---|---|
| Command capture, pending questions, capture history and the records view | internal | 001 | Built |
| An account that owns every memory | internal | 002 | Built |
| A model boundary with per-user attribution and quota | internal | 000 | Built |
| Model provider data terms fit for this data | vendor | user | Open as product Q10 |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Forget leaves the fact recoverable somewhere | high, as built today | high | FR-22, FR-23, FR-28 and NFR-2, with FR-29 disclosing backups honestly |
| `/forget` picks the wrong memory and the user confirms without reading | medium | high | FR-24 and FR-25 name the full text before anything goes |
| The conflict check over-flags and users click through | medium | medium | FR-11's "both are correct", NFR-7, and the conflict-answer metric |
| The conflict check misses a contradiction | medium | medium | NFR-7. Edit or forget remains available |
| Saves grow slow or costly as memories accumulate | medium over time | medium | NFR-4 at 1,000 memories. The build plan states cost per save |
| Keyword-only lookup disappoints | medium | medium | Non-goal stated plainly. 005 adds meaning |
| Users store secrets | medium | high | FR-8's caution, NFR-3 |

## 11. Open questions

| # | Question | Blocks | Owner | Answer |
|---|---|---|---|---|
| ~~Q1~~ | How long can a memory be? | PRD | user | **Answered 2026-09-25.** 500 characters. FR-4 |
| ~~Q2~~ | Can a memory be saved while the model is down? | PRD | user | **Answered 2026-09-25.** No. Refuse and keep the text. FR-9 |
| ~~Q3~~ | What does capture history show where a forgotten memory was saved? | PRD | user | **Answered 2026-09-25.** A placeholder, no words. FR-23 |
| ~~Q4~~ | How are backups handled after forget? | PRD | user | **Answered 2026-09-25.** Disclose the retention window. FR-29 |
| ~~Q5~~ | Are NFR-4 to NFR-7's numbers acceptable? | build plan | user | **NFR-4 answered 2026-09-25:** 8 s, matching 001. NFR-5 to NFR-7 kept as drafted, answered in the build plan's Q6 the same day |
| Q6 | What is the backup retention window FR-29 states? | build plan | tech-stack | Open |

## 12. Out of scope

- Automatic memory, meaning-based lookup and written answers. 005.
- Memories as context for other captures. 005.
- A `/memory` command. It falls to 001's FR-12, which suggests `/memories`.
- Reminders or events from dated memories.
- Scrubbing backups. Disclosed, per FR-29.
- Sharing memories. One account, one owner.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-25 | Created | Drafted after epic approval and PRD questions Q1 to Q4 were answered | pending |
| 2026-09-25 | Approved | User approved, proceed to design | user |
| 2026-09-25 | NFR-4 revised from 2 s to 8 s at p95, and Q5 updated. Found while drafting the build plan: every save needs a model call, measured at 5.3 to 8.5 s in 001. Stale downstream: none. The approved design already shows 001's loading turn during a save, and no screen promises a time | User chose to match 001's 8 s budget | user |
| 2026-09-25 | G4 and its metric now count any memory save within five minutes of a forget, not a similar one. Q5 closed: NFR-5 to NFR-7 stand. Stale downstream: none; the design draws no metric | Build plan Q8: the tombstone erases the text a similarity check would need. User accepted | user |
