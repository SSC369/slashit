---
doc: implementation-plan
feature: 005-personal-search-and-context
title: Personal Search and Context
stage: 4
status: approved
owner: user
created: 2026-09-30
updated: 2026-09-30
approved_on: 2026-09-30
supersedes: null
split: true
---

# Implementation Plan (LLD) — Personal Search and Context

> **Approved** by @user on 2026-09-30. Locked — changes require a change record (§7).

Context: [PRD](./01-prd.md) · [Design](./02-design.md) · [Build plan](./03-build-plan.md)

No code is written before this index and a slice's own sub-plan are approved.

Tables this feature touches, by migration:

| Table | New or changed | Migration | Slice |
|---|---|---|---|
| `tasks` | changed: `search_vector` generated from `title`, GIN index; `embedding vector(768)` | `0032_task_search` | 1 |
| `reminders` | changed: the same, from `description` | `0033_reminder_search` | 1 |
| `capture_turns` | changed: outcome `searched` | `0034_search_capture` | 1 |
| `pending_captures` | changed: `missing_field` value `search_text` | `0034_search_capture` | 1 |
| `events` | changed: `search_run`, `search_result_opened`, `answer_citation_opened`, `related_opened` | `0035_search_events` | 1 |
| `events` | changed: `properties jsonb`, numbers only | `0036_event_properties` | 2 |

The first four migrations are slice 1's. The last two event types stay unused until
their slice. `0036` was added by change record on 2026-09-30.

## 1. Scope recap

Everything in the approved PRD ships, in three slices. Slice 1 is `/search`
by words and meaning across tasks, reminders and memories, grouped by type,
with every existing record made searchable. Slice 2 adds the written answer
with citations. Slice 3 moves the records view search onto the same matching
and adds related records to every detail.

Each slice can reach users alone. Slice 1 without slice 2 answers no question
in sentences, which the PRD allows only as a stage: FR-15 is a must, so 005 is
not marked shipped until slice 2 lands.

## 2. Split decision

| Trigger | Threshold | This feature |
|---|---|---|
| Tasks in the breakdown | more than 15 | about 40, `estimate` |
| Files created or modified | more than 25 | about 75, `estimate` |
| Independently shippable slices | more than one | three |
| Distinct boundaries touched | more than two | seven: search, capture, records, reminders, memories, analytics, worker |
| Length of the drafted plan | more than 500 lines | over, as one document |

**Decision:** split into three sub-plans. 4.2 and 4.3 are drafted as the slice
before each lands, as 003 and 004 did.

### Slices

| # | Sub-plan | What works when it lands | Depends on | Status |
|---|---|---|---|---|
| 1 | [04.1-search-by-words-and-meaning.md](./04.1-search-by-words-and-meaning.md) | `/search` returns grouped, ranked records by word and meaning; no argument, too long, no match and meaning-unavailable states; history Run again; existing records backfilled; new and edited records embedded | — | approved 2026-09-30 |
| 2 | [04.2-written-answer.md](./04.2-written-answer.md) | A question gets a cited answer, the no-support sentence, or the answer-unavailable strip; citations open records | 1 | approved 2026-09-30 |
| 3 | [04.3-records-search-and-related.md](./04.3-records-search-and-related.md) | The records view search uses slice 1's ranking; a record's detail lists related records with every drawn state | 1 | approved 2026-09-30 |

Slices 2 and 3 are independent of each other. 2 goes first because FR-15 is a
must and 001's Q14 was closed on it.

## 3. How the build plan maps to the code

Two refinements of the build plan, neither changing a decision:

| Build plan says | The code does | Why |
|---|---|---|
| AD-1: "each record domain implements `SearchPort` in an adapter" | Each record domain publishes `search_candidates` and `embedding_of` on its service in `public.py`. The adapters implementing `SearchPort` live in `search/adapters/` | Repo rules §6: the consuming domain declares the port and writes the adapter against the provider's `public.py` |
| §3: search reuses 004's term handling | `search/services/terms.py` holds its own copy of 004's term rule. A unit test pins both to the same output on a shared sample | `core/` may not hold business logic, and memories' `/memories` stays exactly as 004 shipped it |

Dependency graph after 005, acyclic:

```
capture  -> search, records, reminders, memories, gateway
search   -> records, reminders, memories, gateway, analytics
records  -> reminders, memories, gateway, analytics
```

## 4. Shared file map

Only the files more than one slice changes.

| Path | Slice 1 | Slice 2 | Slice 3 |
|---|---|---|---|
| `backend/app/domains/search/public.py` | created | answer types | related, page types |
| `backend/app/domains/search/services/search_service.py` | created | `answer_question` | `search_page`, `related` |
| `backend/app/domains/search/graphql/types.py` | created | `SearchAnswer` | `SearchPage`, `relatedRecords` |
| `backend/app/domains/capture/graphql/types.py` | `SearchResults`, `SearchTooLong` | answer fields | — |
| `backend/app/core/deps.py` | search wiring, embed queues | answer port | — |
| `backend/app/graphql/schema.py` | search types registered | — | `search`, `relatedRecords` queries |
| `frontend/src/features/capture/components/SearchCards.tsx` | created | answer block | — |
| `frontend/src/api/mutations/SubmitCapture/operation.graphql` | search fields | answer fields | — |

## 5. Interfaces and contracts

Python signatures are keyword-only, per `backend/.claude/rules/code-rules.md`.

### Record types and candidates, slice 1

```python
# search/public.py
class RecordType(StrEnum): TASK = "task"; REMINDER = "reminder"; MEMORY = "memory"

@dataclass(frozen=True)
class SearchCandidate:
    record_type: RecordType
    record_id: UUID
    item: TaskDTO | ReminderDTO | MemoryDTO   # each domain's own public DTO
    all_terms: bool                           # every term present
    word_rank: float | None                   # ts_rank; None if no term present
    distance: float | None                    # cosine; None if no vector or no query vector
```

### The search port, slice 1

```python
# search/interfaces/ports.py
class SearchPort(Protocol):
    record_type: RecordType
    async def search_candidates(
        self, *, user_id: UUID, terms: list[str],
        embedding: tuple[float, ...] | None, max_distance: float, limit: int,
    ) -> tuple[list[SearchCandidate], int]: ...   # candidates, total matches
    async def embedding_of(self, *, user_id: UUID, record_id: UUID) -> tuple[float, ...] | None: ...
```

A record matches when any term is present or its distance is under
`max_distance`. Deleted rows never match. Every call runs in the user's RLS
transaction. `embedding_of` is used by slice 3 only.

### Published record-domain methods, slice 1

```python
# records/public.py        RecordsService.search_candidates(...), .embedding_of(...)
# reminders/public.py      ReminderService.search_candidates(...), .embedding_of(...)
# memories/public.py       MemoryService.search_candidates(...), .embedding_of(...)
```

Same parameters as the port, returning the domain's own rows with the three
scores. Ranking is search's job, never a record domain's.

### Search results, slice 1

```python
@dataclass(frozen=True)
class SearchHitDTO:
    record_type: RecordType; item: TaskDTO | ReminderDTO | MemoryDTO
    citation: int | None            # always None until slice 2

@dataclass(frozen=True)
class SearchGroupDTO:
    record_type: RecordType; hits: list[SearchHitDTO]; total: int   # hits <= 5

@dataclass(frozen=True)
class SearchResultsDTO:
    query: str; groups: list[SearchGroupDTO]   # ordered by each group's best hit
    meaning_unavailable: bool

SearchService.search_for_capture(*, user_id: UUID, text: str) -> SearchResultsDTO
```

Slice 2 adds `answer: SearchAnswerDTO | None`, `no_support: bool` and
`answer_unavailable: bool` to `SearchResultsDTO`. Slice 3 adds
`search_page(...)` and `related(...)`.

### Ranking, slice 1, used by all three

```python
# search/services/ranking.py  (AD-3)
def rank_key(c: SearchCandidate) -> tuple:
    tier = 2 if c.all_terms else 1 if c.word_rank is not None else 0
    return (-tier, -(c.word_rank or 0.0), c.distance if c.distance is not None else 9.0)
```

`MEANING_MAX_DISTANCE = 0.35` and `RELATED_MAX_DISTANCE = 0.30`, both in
`search/constants.py` and both `estimate` until the evaluation sets in §7 tune them.

### GraphQL, for the frontend

| Type or field | Slice |
|---|---|
| `SearchResults { query groups { recordType total hits { citation record } } meaningUnavailable }`, where `record` is the existing `RecordItem` union | 1 |
| `SearchTooLong { length limit }`, `CaptureTurn.outcome` value `SEARCHED` | 1 |
| `SearchResults.answer { sentences { text citations } }`, `noSupport`, `answerUnavailable` | 2 |
| `search(text, recordType, offset, limit): SearchPage`, `relatedRecords(recordType, id)` | 3 |

## 6. Rollout and flags

No flag. Each slice merges to `main` when its own definition of done holds.

Deploy steps for slice 1, in order:

1. Migrations `0032` to `0035` run forward. Each has a working `downgrade`
   for development.
2. The worker restarts, registering the two embed jobs and two backfill jobs.
3. `records.backfill_embeddings(full=True)` and
   `reminders.backfill_embeddings(full=True)` are deferred once, by hand,
   from the worker container. They throttle to five calls a second, `estimate`,
   and the ten-minute periodic run finishes anything left (FR-13).

## 7. Evaluation sets

The build plan's risks commit to tuning AD-3 and AD-6 on labelled sets, during
slice 1 and before 4.3's approval, per its change record of 2026-09-30. All
live in `backend/tests/eval/` as JSON and run as live tests, never in CI.

| Set | Size | Owner | Needed by |
|---|---|---|---|
| Search: a seeded account of about 150 records, 40 word queries and 30 meaning queries, each with its expected record | 70 queries, `estimate` | Claude drafts, user corrects | End of slice 1: NFR-6, NFR-7, tunes `MEANING_MAX_DISTANCE` |
| Answers: 30 questions over the same account, with the records a correct answer cites, 8 of them unanswerable | 30, `estimate` | Claude drafts, user corrects | 4.2 approval: NFR-8 |
| Related: 25 records from the same account, each with the records a person would call related | 25, `estimate` | Claude drafts, user corrects | 4.3 approval: NFR-9, tunes `RELATED_MAX_DISTANCE` |

## 8. Definition of done, for the feature

- Every task in 04.1 to 04.3 is shipped or explicitly dropped in the dev log.
- NFR-1: T7 boundary tests pass for `/search`, the answer prompt, `search` and
  `relatedRecords`, each with user B's ids supplied.
- NFR-2: the logging test passes with search text and record text in every
  logged field (AD-10).
- NFR-3 to NFR-9 measured and recorded in the dev log. NFR-3 and NFR-4
  re-measured from the deployed API with epic 012 (build plan Q6).
- AD-11: the coverage test fails when a record type has no search port.
- The design matches the canvas, or a change record says why not.
- `index.md` shows 005 as shipped.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-30 | Created as the index, with sub-plan 4.1 drafted | Build plan approved; user asked to proceed | pending |
| 2026-09-30 | Evaluation sets built during slice 1, not before this plan's approval; build plan risk row amended to match | User chose it over waiting on about 125 corrected examples | user |
| 2026-09-30 | Approved | User: "Approved, commit and push" | user |

| 2026-09-30 | `0036_event_properties` added to slice 2: `events` gains a numbers-only `properties` column, so search events carry counts and positions (build plan §3). Re-opens: none; 4.2 is not yet drafted | Dev log Q1: the table held only a type and a time. User chose the column over dropping the metrics | user, 2026-09-30 |
| 2026-09-30 | Slice 3 contracts: `search` returns `SearchPage \| SearchTooLong`, and `SearchPage` gains `query` and `otherTypesTotal` for the drawn "filtered, no match" state. §7: `RELATED_MAX_DISTANCE` is tuned on the related set during slice 3, not before 4.3's approval, as slice 1 did for search. Re-opens: none; 4.3 is the only dependant and is in review | User answered 4.3's question 4; the "{n} other records match" copy needs the count | user, 2026-09-30, with 4.3 |
