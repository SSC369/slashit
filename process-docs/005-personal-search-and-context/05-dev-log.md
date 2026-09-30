---
doc: dev-log
feature: 005-personal-search-and-context
title: Personal Search and Context
stage: 5
status: draft
owner: claude
created: 2026-09-30
updated: 2026-09-30
approved_on: null
supersedes: null
---

# Dev Log — Personal Search and Context

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-search-by-words-and-meaning.md)

What actually happened. Deviations from the approved plan are recorded the day
they happen, per rule 5 of the root ruleset.

## Base

Branch `claude/next-feature-planning-qbpxr3`, from `main` at `af6f4d3` (epic 004
merged). Before any 005 code: local PostgreSQL 16 with pgvector and a stub
Supabase `auth` schema, migrations to `0031` applied, **370 backend tests
passing**, `mypy app` and `ruff check` clean. `ruff format --check` already
listed 8 files; none is touched by this feature and they are left as found.

## Summary

| Slice | What a user can do | Tests at the end of the slice |
|---|---|---|
| Base | — | 370 backend |
| 1 Search by words and meaning | `/search` across tasks, reminders and memories, grouped and ranked by words and meaning; the no-argument, too-long, no-match and meaning-unavailable states; history with Run again; every task and reminder embedded on save and edit, with a backfill | 435 backend, 234 frontend |

Built and verified against a real local PostgreSQL 16 with pgvector, and in
unit and component tests. The model is faked at `LangChainGeminiProvider` in
integration tests. **Not yet verified against the real model, a real project,
or live in a browser**: T-1.13, T-1.14 and the deploy steps are owed.

## Slice 1 — Search by words and meaning

### Tasks

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|
| T-1.1 | 4.1 | Search evaluation set | done | `backend/tests/eval/search_queries.json`: 100 records, 40 word and 30 meaning queries. Each meaning query is checked by script to share no word, not even a five-letter stem, with its target. Accepted by the user as drafted, 2026-09-30. D-10 |
| T-1.2 | 4.1 | Migrations `0032` to `0035` | done | Each run up, down and up again |
| T-1.3 | 4.1 | Task and reminder search columns and queries | done | C-8 |
| T-1.4 | 4.1 | Memories search query and `embedding_of` | done | C-8 |
| T-1.5 | 4.1 | Embed queues, jobs and interactors; an edit clears the vector | done | C-9. D-4 |
| T-1.6 | 4.1 | Backfill jobs, periodic and full | done | C-10. D-5 |
| T-1.7 | 4.1 | `search` domain | done | C-1 to C-4b, C-12. D-1 to D-3 |
| T-1.8 | 4.1 | Capture `/search`, pending question, turn outcome, GraphQL | done | C-5 to C-7, unit and through GraphQL. D-7, D-8 |
| T-1.9 | 4.1 | Analytics events and log redaction | **partial** | C-13 passes; `search_run` recorded. Counts and positions arrive with slice 2's `events.properties` column (Q1, answered) |
| T-1.10 | 4.1 | Boundary tests | done | C-11 |
| T-1.11 | 4.1 | Frontend card, palette, TurnCard routing, styles | done | C-16. Not yet compared against the canvas in a running app: T-1.14 |
| T-1.12 | 4.1 | Frontend history Run again | done | C-17 |
| T-1.13 | 4.1 | Latency and evaluation runs, thresholds tuned | **owed** | `test_search_latency_live.py` (C-14) and `test_search_eval_live.py` (C-15) written and collected; they call the real model, and this environment has no provider key. `MEANING_MAX_DISTANCE` stays 0.35, `estimate`, until they run |
| T-1.14 | 4.1 | Live browser pass against a real project | **owed** | No Supabase project credentials reachable from this environment, as 003 and 004 recorded |

### Test cases

| Case | Where | Result |
|---|---|---|
| C-1, C-2 | `unit/test_search_ranking.py` | pass, 5 |
| C-3 | `unit/test_search_terms.py` | pass, 21 |
| C-4, C-4b, C-12 | `unit/test_search_service.py` | pass, 5 |
| C-5 to C-7 | `unit/test_search_capture.py`; `integration/test_search_graphql.py` | pass, 6 and 7 |
| C-8 | `integration/test_search_ports_db.py` | pass, 6 |
| C-9 | `unit/test_task_embedding.py`; three cases in `unit/test_reminder_interactors.py` | pass, 5 and 3 |
| C-10 | `integration/test_search_backfill_db.py` | pass, 4 |
| C-11 | `integration/test_search_boundary.py` | pass, 2: user B searches user A's exact title and its meaning, and gets nothing |
| C-13 | `test_logging_redaction.py` | pass |
| C-14, C-15 | `integration/test_search_latency_live.py`, `integration/test_search_eval_live.py` | owed, T-1.13 |
| C-16 | `SearchCards.test.tsx`; response handler cases for both new union members | pass |
| C-17 | `HistoryPanel.test.tsx` | pass |

### Deviations from the plan

All recorded 2026-09-30. None changes a locked decision; each is a detail the
plan left open or stated wrongly. All eleven approved by the user on
2026-09-30.

| # | Planned | Actual | Why | Approved by |
|---|---|---|---|---|
| D-1 | Build plan AD-1, index §5: each record domain owns its search SQL | Each still owns its query, but the word and meaning expressions come from one helper, `app/core/text_search.py` | Three copies of the same `to_tsquery` and distance construction would drift. The helper decides nothing, which is what `core/` may hold | user, 2026-09-30 |
| D-2 | 4.1 §5: a meaning pass, then a merge by record id in Python | With a query vector, one SQL pass matches by words and meaning together and replaces the word-only results | The same records and scores, with the merge done by the database. AD-4's overlap of embed and word pass holds (C-4b) | user, 2026-09-30 |
| D-3 | 4.1 §4: ports fanned out with `asyncio.gather` | The three ports run one after another; the query embed runs alongside the whole word pass | The ports share the request's database session, which runs one query at a time | user, 2026-09-30 |
| D-4 | 4.1 §4: "`update` sets `embedding = None` when the title changes" | A SQL `CASE` clears the vector only when the text actually changes. The job embeds only a record whose vector is still empty, and stores it only if the text is still the one embedded | An edit form that resends the same title costs no model call, and a vector computed before a later edit is never written over it | user, 2026-09-30 |
| D-5 | Index §6: the full backfill throttles to about five a second "and the periodic run finishes anything left" | The full sweep walks every page itself, by id, and spaces its jobs at five a second | The periodic sweep only sees the last 24 hours, as 004's does, so it could never finish the old rows the plan relied on it for | user, 2026-09-30 |
| D-6 | Not stated | The embed queues also log and swallow `AppNotOpen`, as they swallow a connection error | A process that never opened the queue, such as an unrelated GraphQL test, must not fail a task save. The periodic backfill queues the vector within ten minutes | user, 2026-09-30 |
| D-7 | Not stated | `/search` is exempt from capture's 500-character line cap, with the 1,000-character outer guard, as a memory save is (004 AD-7) | FR-3 needs a drawn "too long" state for text over 500, which the line cap would turn into a client error | user, 2026-09-30 |
| D-8 | FR-21: history keeps "the typed search line" | An answered "What should Slashit search for?" is kept as `/search <answer>` | The typed line was `/search` alone, and Run again would only ask the question again | user, 2026-09-30 |
| D-9 | Build plan §3, index §5: events carry counts, types and positions | Only `search_run` is recorded, with no counts. `search_result_opened` is not recorded yet | The `events` table has a type and a time and nothing else. Storing a position needs a column no plan names. Q1 below | user, 2026-09-30 |
| D-10 | Index §7: about 150 records | 100 records, 40 word and 30 meaning queries | Enough for the two rates to move by 2.5 and 3.3 points per miss; more can be added during correction | user, 2026-09-30 |
| D-11 | 4.1 §4: `search/graphql/types.py` | The GraphQL types live in `search/interfaces/dtos.py`; `search` has no `graphql/` folder until slice 3 adds its queries | Capture's result union carries them, and repo-rules §6.2 lets only `interfaces/` cross a boundary, as records does for `Task` | user, 2026-09-30 |

### Incidents and defects

| Date | What broke | Cause | Fix |
|---|---|---|---|
| 2026-09-30 | `alembic upgrade head` failed on a fresh database at `0031` | Pre-existing: alembic runs every migration in one transaction, and `0031` uses an enum value `0028` added in the same transaction. Databases migrated step by step never hit it | Not changed here. Upgrading to `0030` first, then `head`, works. Raised for epic 012, which will build a fresh production database |
| 2026-09-30 | Every search with only words, or only a vector, failed in PostgreSQL | A constant, `false` or `NULL`, in `ORDER BY` | The helper builds the sort from the parts that vary only |
| 2026-09-30 | A text substitution put the empty-vector condition on `get_embedding` instead of the embed job's read | Pattern matched the first of two similar methods | Moved before any test ran; C-8 and C-9 cover both methods |

### Questions for the user

| # | Question | Blocks | Answer |
|---|---|---|---|
| ~~Q1~~ | How should search events carry counts and positions? | T-1.9, 4.2 | **Answered 2026-09-30.** Add a numbers-only `properties` column to `events`, in slice 2, with a test that it never holds text. Index change record the same day |

## Remaining work

| Item | Needs | Owner |
|---|---|---|
| T-1.13 | A provider key: run `pytest -m live tests/integration/test_search_eval_live.py tests/integration/test_search_latency_live.py`, then set `MEANING_MAX_DISTANCE` from the misses | Claude, with the key |
| T-1.14 | A real project: every slice 1 artboard compared in the running app | Claude, with project access |
| Deploy steps | Index §6: migrations, worker restart, and the one-off `full=True` backfill for both record types | Claude, at deploy |
| Search event counts and positions | Slice 2's `properties` column (Q1) | Claude, in 4.2 |
