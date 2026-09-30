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

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-search-by-words-and-meaning.md) ·
[04.2](./04.2-written-answer.md) · [04.3](./04.3-records-search-and-related.md)

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
| 2 Written answer | A question gets at most four cited sentences above the groups, with markers on the cited rows; the no-support and answer-unavailable states; the question loading card; search events carry counts and positions | 484 backend, 252 frontend |
| 3 Records view search and related | The records view's box searches as `/search` does, on every tab, with the drawn states, a date toggle and Show more; every detail lists up to five related records | 501 backend, 271 frontend |

Built and verified against a real local PostgreSQL 16 with pgvector, and in
unit and component tests. The model is faked at `LangChainGeminiProvider` in
integration tests. **Not yet verified against the real model, a real project,
or live in a browser**: T-1.13, T-1.14, T-2.9, T-2.10, T-3.9's quality run,
T-3.10 and the deploy steps are owed.

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
| T-1.9 | 4.1 | Analytics events and log redaction | done | C-13 passes; `search_run` recorded. Counts and positions completed in slice 2, T-2.2 and T-2.8 |
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
| D-9 | Build plan §3, index §5: events carry counts, types and positions | Only `search_run` is recorded, with no counts. `search_result_opened` is not recorded yet | The `events` table has a type and a time and nothing else. Storing a position needs a column no plan names. Q1 below. Closed by slice 2 | user, 2026-09-30 |
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

## Slice 2 — Written answer

### Tasks

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|
| T-2.1 | 4.2 | Answer evaluation set | done | `backend/tests/eval/search_answers.json`: 30 questions, 8 unanswerable, asked over slice 1's 100 records. Accepted by the user as drafted, 2026-09-30 |
| T-2.2 | 4.2 | Migration `0036` and the analytics changes | done | C-2.11. Run down and up again. Two defects found and fixed before any commit, see Incidents |
| T-2.3 | 4.2 | `is_question`, `check_answer`, pinning | done | C-2.1 to C-2.5. D-13, D-14 |
| T-2.4 | 4.2 | Answer and today ports, adapters, service wiring | done | C-2.6 to C-2.8. D-12 |
| T-2.5 | 4.2 | GraphQL answer fields, `recordSearchEvent` | done | C-2.9, C-2.11 |
| T-2.6 | 4.2 | Boundary case | done | C-2.10 |
| T-2.7 | 4.2 | Frontend answer block, markers, states, loading | done | C-2.14. D-15, D-16. Result rows are now reachable by Tab and open on Enter, which the design's keyboard path asks for and slice 1 missed. Not yet compared against the canvas in a running app: T-2.10 |
| T-2.8 | 4.2 | Frontend events | done | C-2.15. D-17 |
| T-2.9 | 4.2 | Live answer quality and latency runs | **owed** | `test_search_answer_eval_live.py` (C-2.13) and a question case in `test_search_latency_live.py` (C-2.12) written and collected. No provider key here. C-2.13 also asserts at most two of the eight unanswerable questions get an answer, `estimate`: the PRD sets no rate for FR-18 |
| T-2.10 | 4.2 | Live browser pass | **owed** | No project credentials reachable, as T-1.14 |

### Test cases

| Case | Where | Result |
|---|---|---|
| C-2.1 | `unit/test_search_question.py` | pass, 23 |
| C-2.2 to C-2.4 | `unit/test_answer_check.py` | pass, 6 |
| C-2.5 | `unit/test_search_ranking.py` | pass, 6 in the file, 1 new |
| C-2.6, C-2.7 | `unit/test_search_service.py` | pass, 4 new: word search never calls the model, cited answer, failed answer keeps records, no records needs no model call |
| C-2.8 | `unit/test_gateway_answer_adapter.py` | pass, 3 |
| C-2.9 | `integration/test_search_graphql.py` | pass, 4 new: answered with a marked row, word search writes no answer, no support, answer unavailable |
| C-2.10 | `integration/test_search_boundary.py` | pass: user B's question never puts user A's record in the prompt |
| C-2.11 | `integration/test_search_events_db.py` | pass, 7: a string, a nested object, an array inside a value and a top-level array are refused; numbers and booleans accepted; an event without properties stores SQL `NULL`; `recordSearchEvent` stores a position and a citation |
| C-2.12, C-2.13 | `integration/test_search_latency_live.py`, `integration/test_search_answer_eval_live.py` | owed, T-2.9 |
| C-2.14 | `SearchCards.test.tsx`; `utils/isSearchQuestion.test.ts` | pass, 8 new and 9 |
| C-2.15 | `RecordSearchEvent/responseHandler.test.ts`; `CommandCenterController.test.tsx` | pass, 2 and 2 |

### Deviations from the plan

All recorded 2026-09-30. D-15 changes approved copy, recorded in the design's
change log; the others are details the plan left open or stated wrongly. All
six approved by the user on 2026-09-30.

| # | Planned | Actual | Why | Approved by |
|---|---|---|---|---|
| D-12 | 4.2 §5: `UserTodayPort.today_for_user` returns the user's date | `UserTimezonePort.get_user_timezone` returns the zone, and the service takes today from an injected `now_provider` | The prompt's record details ("due Mon 13 Oct") need the zone too, not only the date; one read serves both. The clock is injected so tests fix it | user, 2026-09-30 |
| D-13 | 4.2 §4: a separate `pin_cited(*, groups, cited, limit)` | Pinning happens inside `group_hits`, which now takes the citations | The five shown are chosen once, with the cited ones first to keep and the lowest uncited dropped. A second pass after grouping would re-sort and could lose the order | user, 2026-09-30 |
| D-14 | 4.2 §5: `check_answer(*, draft, records)` returns a `CheckedAnswer` | It takes `record_count` and returns `None` for no support | The check needs only how many records were numbered. `None` makes the no-support path a type the service must handle | user, 2026-09-30 |
| D-15 | Design §8 copy: "Nothing you have saved says {what was asked}." | "Nothing you have saved answers “{the question as typed}”." | The server returns no rephrasing of the question. Writing one would be model text outside a cited sentence, which FR-18 forbids ("states nothing else"). Q2 below | user, 2026-09-30 |
| D-16 | Design `Main`: the answer label's burst glyph | The icon set's `Sparkles` | The drawn glyph is not in the icon set, and its nearest match is a loading spinner | user, 2026-09-30 |
| D-17 | 4.2 §7, C-2.15: "both new handler members" | Slice 2 adds no union member. The answer rides on `SearchResults`; C-2.15 covers the new mutation's handler and the controller's two events | The plan assumed new members that the contract never needed | user, 2026-09-30 |

`core/logging.py` needed no change: slice 1 already redacts the `question` and
`sentences` keys.

### Incidents and defects

| Date | What broke | Cause | Fix |
|---|---|---|---|
| 2026-09-30 | The numbers-only check let `{"list": [1, 2]}` through | A lax-mode JSON path unwraps an array into its members, so each member passed as a number | The check uses a `strict` path. C-2.11 case |
| 2026-09-30 | Every existing event write, such as `records_view_opened`, failed the new check | The ORM wrote a Python `None` as the JSON value `null`, which is not an object | The column stores `None` as SQL `NULL`. Caught by 003's own test before any commit; C-2.11 now covers it |

### Questions for the user

| # | Question | Blocks | Answer |
|---|---|---|---|
| ~~Q2~~ | D-15: how should the no-support sentence name the question? Options: (a) quote the question as typed, as built (Recommended); (b) a model rephrase; (c) drop the question | Design match for `SearchNoSupport` | **Answered 2026-09-30.** (a), quote as typed. Design change record the same day |

## Slice 3 — Records view search and related records

### Tasks

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|
| T-3.1 | 4.3 | Related evaluation set | done | `backend/tests/eval/related_records.json`, 25 records. Accepted by the user as drafted, 2026-09-30 |
| T-3.2 | 4.3 | `search_page`, `SearchRecordsInteractor`, `search` query | done | C-3.1 to C-3.4. `/search` and `search` share one words-and-meaning pass |
| T-3.3 | 4.3 | `related`, `ListRelatedRecordsInteractor`, `relatedRecords` query | done | C-3.6, C-3.7 |
| T-3.4 | 4.3 | Retire `records(filter.search)` | done | C-3.5. D-18, D-21 |
| T-3.5 | 4.3 | `related_opened` event | done | C-3.9 |
| T-3.6 | 4.3 | Boundary cases | done | C-3.8 |
| T-3.7 | 4.3 | Frontend records view search | done | C-3.10. D-19, D-20. Not yet compared against the canvas in a running app: T-3.10 |
| T-3.8 | 4.3 | Frontend related section on three details | done | C-3.11 |
| T-3.9 | 4.3 | Related latency run; quality run and tuning | **partial** | C-3.12 run here, no key needed: at 3,000 records, median 0.063 s, p95 0.075 s over 20 lists, against the local database. C-3.13 written and collected; it needs real vectors and no provider key is reachable. `RELATED_MAX_DISTANCE` stays 0.30, `estimate` |
| T-3.10 | 4.3 | Live browser pass | **owed** | No project credentials reachable, as T-1.14 |

### Test cases

| Case | Where | Result |
|---|---|---|
| C-3.1 | `unit/test_search_service.py` | pass, 3 new |
| C-3.2 to C-3.5, C-3.7 | `integration/test_search_records_graphql.py` | pass, 11 |
| C-3.6 | `unit/test_search_related.py` | pass, 3 |
| C-3.8 | `integration/test_search_boundary.py` | pass: user B, holding the same records as A, finds only B's, and A's id gives B an empty related list |
| C-3.9 | `integration/test_search_events_db.py` | pass |
| C-3.10 | `RecordsController.test.tsx`; `RecordsStore.test.ts`; both new query handlers | pass, 8, 3 and 4 |
| C-3.11 | `RelatedRecords.test.tsx`; `MemoryDetailController.test.tsx` | pass, 5 and 1 |
| C-3.12 | `integration/test_search_related_latency.py` | pass, numbers above |
| C-3.13 | `integration/test_search_related_eval_live.py` | owed, T-3.9 |

### Deviations from the plan

All recorded 2026-09-30. All four approved by the user on 2026-09-30.

| # | Planned | Actual | Why | Approved by |
|---|---|---|---|---|
| D-18 | 4.3 §8, T-3.4: "001 and 003 records tests updated, none dropped" | `test_search_matches_title_case_insensitively` is deleted, and the two records view tests for letter-match no-match states are replaced by search-mode ones | Each tested the letter match FR-22 retires. Nothing else was dropped | user, 2026-09-30 |
| D-19 | 4.3 §4: the records view's search states in `RecordsController` plus a `RecordsSearchStates.tsx` component | A `RecordsSearchController` holds the search mode and its states; `RecordsController` routes to it when the box holds text. `RecordTable` gains optional footer props for the search's count and Show more | Every other tab with its own load has its own controller here, as Reminders and Memories do. A states component would only have forwarded props | user, 2026-09-30 |
| D-20 | Design `RecordsSearchStates`: the drawn states | Two more, not drawn: a category chip that hides every memory match ("No memories in this category match “{text}”" · "Choose All to see every match."), and text over 500 characters. The box also stops at 500, so the second is reached only by a bypassed client | Q3's answer makes the first possible; the second is `search`'s union member, and every member is handled | user, 2026-09-30 |
| D-21 | 4.3 §4 assumption: `reminders(search)` and `memories(filter.search)` stay | They stay, and so does the search code in `RemindersController` and `MemoriesController`, now unreachable: those tabs render only with an empty box. The records adapters pass `search=None` to both services | Removing them belongs to 003 and 004's surfaces. A follow-up, not this slice | user, 2026-09-30 |

### Incidents and defects

| Date | What broke | Cause | Fix |
|---|---|---|---|
| 2026-09-30 | `errorLink.test.ts` fails as a suite, in slice 2's run and this one | Pre-existing: its mock loads the real `sessionExpiry`, which needs `VITE_SUPABASE_*` set, and this environment has none. It fails the same on a clean checkout of `736b124`, whose frontend is `4455b4d`'s | Not changed here. Slice 2's summary counted tests, not suites, so it was missed there |
| 2026-09-30 | `ruff format` on the records adapters folder rewrote `analytics_event_adapter.py`, one of the files left as found | Formatted a folder, not the changed files | Reverted before any commit |

## Remaining work

| Item | Needs | Owner |
|---|---|---|
| T-1.13 | A provider key: run `pytest -m live tests/integration/test_search_eval_live.py tests/integration/test_search_latency_live.py`, then set `MEANING_MAX_DISTANCE` from the misses | Claude, with the key |
| T-1.14 | A real project: every slice 1 artboard compared in the running app | Claude, with project access |
| Deploy steps | Index §6: migrations, worker restart, and the one-off `full=True` backfill for both record types | Claude, at deploy |
| T-2.9 | A provider key: run `pytest -m live tests/integration/test_search_answer_eval_live.py tests/integration/test_search_latency_live.py`, then judge each printed citation by hand for NFR-8 | Claude with the key, then the user |
| T-2.10 | A real project: `Main`, `SearchNoSupport`, `SearchDegraded` and `SearchStates` compared in the running app | Claude, with project access |
| T-3.9, quality | A provider key: run `pytest -m live tests/integration/test_search_related_eval_live.py`, judge each `?` row by hand, then set `RELATED_MAX_DISTANCE` | Claude with the key, then the user |
| T-3.10 | A real project: `RecordsSearch`, `RecordsSearchStates`, `RelatedDetail` and `RelatedStates` compared in the running app | Claude, with project access |
