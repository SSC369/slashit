---
doc: dev-log
feature: 005-personal-search-and-context
title: Personal Search and Context
stage: 5
status: shipped
owner: claude
created: 2026-09-30
updated: 2026-10-02
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
listed 8 files; none is touched by this feature. They were left as found
until PR #2, whose CI stopped at that same check. The user chose to format
the 7 still listed there on 2026-09-30; each file's syntax tree is unchanged.

## Summary

| Slice | What a user can do | Tests at the end of the slice |
|---|---|---|
| Base | — | 370 backend |
| 1 Search by words and meaning | `/search` across tasks, reminders and memories, grouped and ranked by words and meaning; the no-argument, too-long, no-match and meaning-unavailable states; history with Run again; every task and reminder embedded on save and edit, with a backfill | 435 backend, 234 frontend |
| 2 Written answer | A question gets at most four cited sentences above the groups, with markers on the cited rows; the no-support and answer-unavailable states; the question loading card; search events carry counts and positions | 484 backend, 252 frontend |
| 3 Records view search and related | The records view's box searches as `/search` does, on every tab, with the drawn states, a date toggle and Show more; every detail lists up to five related records | 501 backend, 271 frontend |

Built and verified against a real local PostgreSQL 16 with pgvector, and in
unit and component tests. The model is faked at `LangChainGeminiProvider` in
integration tests. The live runs and a first browser pass followed on
2026-10-01, against the real model and the Supabase project: see
[Live runs and browser pass](#live-runs-and-browser-pass-2026-10-01). Two
targets fail there and are parked by the user, so the feature is not shipped.

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
| T-1.13 | 4.1 | Latency and evaluation runs, thresholds tuned | done | NFR-3, NFR-6 and NFR-7 pass. `MEANING_MAX_DISTANCE` 0.40 after D-22, 2026-10-02. See Live runs |
| T-1.14 | 4.1 | Live browser pass against a real project | done | Artboards compared 2026-10-02. `SearchPassport` and the no-match state differ, Q6. See Live runs |

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
| C-14 | `integration/test_search_latency_live.py` | pass, 2026-10-02: p95 2.69 s. The 2026-10-01 run's seed timed out |
| C-15 | `integration/test_search_eval_live.py` | pass at 0.40 after D-22: word 100%, meaning 90%. Before D-22: 10% at 0.35, 87% at 0.48 |
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
| T-2.9 | 4.2 | Live answer quality and latency runs | done | Run 2026-10-01. Answer quality passes. NFR-4 misses and is accepted for V1 (Q5). Citations judged by the user 2026-10-02; D-23 |
| T-2.10 | 4.2 | Live browser pass | done | Compared 2026-10-02. See Live runs |

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
| C-2.12 | `integration/test_search_latency_live.py` | **fail**: p95 10.80 s against 8.0 s. Accepted for V1, Q5 |
| C-2.13 | `integration/test_search_answer_eval_live.py` | pass |
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
| T-3.9 | 4.3 | Related latency run; quality run and tuning | done | C-3.12 at 3,000 records: median 0.063 s, p95 0.075 s, local database. C-3.13 passes; `RELATED_MAX_DISTANCE` 0.20 after D-22, 2026-10-02. See Live runs |
| T-3.10 | 4.3 | Live browser pass | done | Compared 2026-10-02. See Live runs |

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
| C-3.13 | `integration/test_search_related_eval_live.py` | pass at 0.20 after D-22: 55 listed, 80% labelled related, `m-mentor` empty |

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

## Merge to main

Merged through PR #2 on 2026-09-30, at the user's request, with every check
green on the last head.

| Item | Detail |
|---|---|
| Pull request | https://github.com/SSC369/slashit/pull/2 |
| Commits | 12 stage and slice commits, plus the two CI fixes below |
| CI on the last head | Backend lint, types, tests; Secret scan; GitGuardian: all pass |
| Review comments | none |

CI had been red on `main` since before 005, and it stopped at the first
failing step, so each fix exposed the next:

| Commit | What CI hit | Fix |
|---|---|---|
| `45d9125` | `ruff format --check`: the 7 files the Base section lists as unformatted | Formatted, at the user's choice. Each file's syntax tree is unchanged |
| `9c099c6` | The unit tests could not load `Settings`: `SUPABASE_PUBLISHABLE_KEY`, required since 002's `b7efa24`, was never set in CI | A placeholder in `ci.yml`. The key is not a secret. 369 CI tests pass without `backend/.env` |

005 stays **in progress** after the merge. It is not shipped until the owed
live runs and browser passes below are recorded (index §8).

## Follow-ups after the merge

Two cleanups the user asked for on 2026-09-30, on this branch, restarted from
`main` after PR #2 merged.

| Item | What changed | Verified |
|---|---|---|
| D-21's dead search code | `reminders(search)` and `memories(filter.search)` are gone from the schema, with the letter match behind each: the input fields, DTO fields, service and repository parameters, and memories' `_escape_like`. The Reminders and Memories tabs load without text; their unreachable no-match-for-text copy is removed. The Memories tab keeps its category no-match state. `/memories <text>` in capture is untouched: it uses `find_by_terms`, a separate path | 501 backend, none dropped; 274 frontend |
| `errorLink.test.ts` | Stubs `./supabaseClient`, as `sessionExpiry.test.ts` does, so the real client is never built without `VITE_SUPABASE_*` | The suite passes with no env set; all 52 frontend suites pass |

The local database had to be rebuilt first: the container had been reset, and
the stub needed `supabase_auth_admin` as well as the roles listed in Base.

## Live runs and browser pass, 2026-10-01

Run from the user's machine against the real model (`gemini-embedding-001`
and the chat model in `backend/.env`) and the Supabase project, at the user's
direction. Migrations `0032` to `0036` were applied to that project first; it
is now at `0036`. The three runs after T-1.13 ran in parallel, sharing the key
and the database.

### Results

| Case | Target | Measured | Result |
|---|---|---|---|
| C-15, NFR-6 word queries in the top three | > 95% | 98%. The one miss, "passport", ranks the reminder fourth behind two other passport records | pass |
| C-15, NFR-7 meaning queries in the top five | > 80% | 10% at `MEANING_MAX_DISTANCE` 0.35; 87% at 0.48, rerun 2026-10-02 | pass at 0.48 |
| C-14, NFR-3 search at 3,000 records | p95 < 3.0 s | Median 1.94 s, p95 2.69 s over 20, rerun alone 2026-10-02. The 2026-10-01 seed insert timed out under the parallel runs. A first 2026-10-02 rerun stopped when one query embed passed its 2.5 s limit and the search fell back to words | pass |
| C-2.12, NFR-4 question at 3,000 records | p95 < 8.0 s | Median 7.06 s, p95 10.80 s over 20. Search 2.1 to 6.4 s, answer 2.4 to 6.6 s | **fail**, accepted for V1 (Q5) |
| C-2.13, NFR-8 grounded answers | No uncited sentence; refusals as set | 0 uncited sentences. Every unanswerable question refused, every answerable one answered | pass |
| C-3.13, NFR-9 related lists | ≥ 70% labelled related | 100% of 29 listed at 0.30. Five records get an empty list | pass |

### Why NFR-7 fails

Every miss is the cutoff, not the model call: the query vector arrives, and the
target is further than 0.35. Measured with the cutoff lifted:

| Distance | Min | Median | Max |
|---|---|---|---|
| Meaning query to its target | 0.33 | 0.42 | 0.48 |
| Meaning query to the nearest other record | 0.33 | 0.42 | — |

| `MEANING_MAX_DISTANCE` | Meaning hit rate |
|---|---|
| 0.35 | 10% |
| 0.45 | 73% |
| 0.48 | 87% |

At 0.48 almost every record matches almost any query, so `/search` would list
noise below the real hits. The alternative is to embed records and queries
with separate task types, which `gemini-embedding-001` supports; that needs a
model call change, a full re-embed and a rerun. The user chose 0.48 on
2026-10-02 (Q3). The rerun's four misses are vacation, streaming, marriage and
programming, each at 0.46 to 0.48. Its top fives carry the predicted noise:
"streaming" lists the milk task and the bin reminder.

### Related cutoff sweep

From the eval file's labels, with the cutoff lifted, top five per record:

| `RELATED_MAX_DISTANCE` | Labelled related | Labelled pairs found | Empty lists |
|---|---|---|---|
| 0.30 | 100% | 48% | 5 |
| 0.35 | 83% | 72% | 0 |
| 0.36 | 71% | 74% | 0 |

0.35 is recommended. At 0.35 the new unlabelled pairs are family dates
together, SIP with the fixed deposit, passport with car insurance, and the
landlord with the electricity bill. Four labelled pairs sit at 0.43 to 0.54,
past any usable cutoff, so the eval file may be over-labelled. Q4.

### Answer citations to judge

Flagged by Claude; judged by the user for NFR-8 on 2026-10-02.

| Answer | Concern | Verdict |
|---|---|---|
| "Rahul's wedding is in February 2027." | The record says only "February". The year is the model's. Seen in one of two runs | Unsupported. D-23 |
| Passport reminder "on Tuesday 1 December at 9:00 AM"; fixed deposit "the week of Tuesday, December 1" | Taken from the reminder's stored time, not its text | Supported: a reminder's time is part of the record |
| "Scan PAN card and passport" cited for "What do I need to do about my passport?" | Not in the expected citations | Supported |

### Browser pass

In the running app, signed in as the user, over their three records. Each state
behaved as designed; the artboard-by-artboard comparison is still owed.

| Surface | Checked |
|---|---|
| Capture `/search` | No-argument question; a word search; a cited one-sentence answer with its marker on the row; the no-support state quoting the question |
| Records view search | Word match with count and best-match order; no match; a tab with matches only elsewhere ("Show all"); date sort; the box stopping at 500 characters |
| Memory detail | Related section's empty state |

"vehicle" does not find "I love cars", as the NFR-7 numbers predict. No console
errors.

### Artboard comparison, 2026-10-02

The artboards' records were seeded into the user's account through Capture: the
passport set and the career set, 14 records. Each artboard was opened from
`assets/canvas/` beside the running app, dark theme.

| Artboard | Result |
|---|---|
| `Main` / `DarkMain` | Matches: count pill, answer with marker, three groups, footer. The model cited only the memory where the canvas also cites the task |
| `SearchPassport` | **Differs.** 9 records where the canvas has 3: "I love cars", the dentist memory and "capture moon" match by meaning at 0.48 |
| `SearchResults` | Layout matches. 5 records where the canvas has 9: the Spring Boot tasks sit past 0.48. Overflow not reached |
| `SearchStates` | Question loading, no argument and too long match. **No match is barely reachable:** "kayak" returns "Renew passport" and "capture moon". The no-argument card lacks the canvas's example line; §4 names 001's card, which has none |
| `SearchNoSupport` | Matches, with D-15's copy |
| `SearchDiscovery`, `SearchHistory` | Match |
| `RecordsSearch` | Matches, and lists what `/search career` lists (FR-23) |
| `RecordsSearchStates` | No match, filtered no match, date sort match |
| `RelatedDetail` / `RelatedStates` | Match. Two related rows where the canvas has three: the visa task sits past 0.30. Empty state matches |
| `SearchDegraded`, error, offline, no permission | Not reachable without breaking the model or the session; covered by C-16, C-2.14 and C-3.10 |

| Finding | Severity | Owner |
|---|---|---|
| At `MEANING_MAX_DISTANCE` 0.48 a one-word search lists unrelated records, and the no-match state rarely shows. The cost Q3 named, now seen on real data | High: the canvas and FR-10's no-match state no longer hold | user, Q6 |
| The Capture feed does not scroll when a loading card grows into its result, so a long result sits under the input | Medium | Fixed 2026-10-02, see Incidents |
| An answer refused for the daily model allowance shows the "model is unavailable right now… temporary" strip. Reached after seeding spent the user's allowance | Low: the copy is wrong for a limit | user, Q7 |

### Incidents and defects

| Date | What broke | Cause | Fix |
|---|---|---|---|
| 2026-10-01 | A search text with no spaces ran out of its card: the records view's no-match title, the Capture typed-line bubble and input echo, and the Capture no-match pill | No wrap rule on those elements | 2026-10-02: the titles and bubbles wrap anywhere; the pill truncates. `records/components/styles.ts`, `capture/components/styles.ts`, `SearchCards.tsx`. 274 frontend tests pass, `tsc` and `oxlint` clean |
| 2026-10-02 | The Capture feed stayed put when the newest turn's loading card became its result | It scrolled only when a turn was added | `CommandCenterController` also scrolls when the newest turn's status changes. Checked in the running app |
| 2026-10-02 | Scroll containers styled their own overflow, with the browser's default scrollbar | No shared rule | A `scroll` utility in `design-system/tokens.css`, applied to all eight scroll containers; `frontend/rules/repo-rules.md` §11.5 makes it the rule, at the user's direction. 274 frontend tests pass |
| 2026-10-01 | 7 failures and 1 error in 003's `test_firing_and_notifications.py` and `test_timezone_and_hardening.py` | This machine, not the code: `REMINDER_EMAIL_ENABLED=true` in `backend/.env` defers email jobs the tests never open a queue for, and a running worker shared the database | All 11 pass with email off and the worker stopped. The full suite, rerun that way on 2026-10-02, passes 501 |
| 2026-10-01 | The one-off `full=True` backfill was not queued | Claude Code's permission check blocked deferring jobs against the shared project | Queued 2026-10-02 at the user's request. 10 tasks embedded; the reminder and both memories already had vectors |
| 2026-10-02 | `test_forgetting_a_kept_memory_deletes_its_whole_thread` failed: "Qatar" found in `memories.text` | 12 `@rls-test.invalid` users and their eval records were left by live and suite runs cut off before teardown. The test searches every user's rows | The leftover test users deleted; the test passes |

### Embedding purpose and retuning, 2026-10-02

| # | Planned | Actual | Why | Approved by |
|---|---|---|---|---|
| D-22 | Build plan AD-3 and AD-6: one embedding call for records and searches | Records are embedded as documents and searches as queries: `EmbedPurpose` in `gateway/constants.py`, mapped to the provider's `RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY`, passed through `EmbedInteractor.embed(purpose=...)` by all four adapters. `tests/unit/test_embed_purpose.py` covers both | Every vector was embedded as a query, so a short search sat near every short record and 0.48 matched almost everything | user, Q6, 2026-10-02 |

Search cutoff sweep with document vectors, eval set of 100 records:

| `MEANING_MAX_DISTANCE` | Meaning hit rate | Unrelated records within the cutoff, per query |
|---|---|---|
| 0.38 | 70% | 1.2 |
| **0.40** | **90%** | **3.4** |
| 0.42 | 97% | 12.9 |

Related cutoff sweep. Two documents sit closer than a query and a document, so 0.30 fell to 43% labelled related, 125 listed:

| `RELATED_MAX_DISTANCE` | Labelled related | Labelled pairs found | Empty lists |
|---|---|---|---|
| 0.18 | 83% | 57% | 4 |
| **0.20** | **80%** | **72%** | **1** |
| 0.22 | 58% | 80% | 0 |

| Check | Result |
|---|---|
| C-15 at 0.40 | pass: word 100%, meaning 90%. Misses: streaming, investment, marriage |
| C-3.13 at 0.20 | pass: 55 listed, 80%, `m-mentor` empty. `test_search_related.py`'s fixture distances rescaled under the new cutoff |
| 004 memory tests on document vectors | pass: 100% of 14 conflicts caught, 0.3% of 386 other pairs flagged; NFR-6 categorisation 87% |
| Re-embed | Every live record in the Supabase project re-embedded as a document by a one-off script: 19 tasks, 2 reminders, 5 memories, none failed after one retry. A production database needs the same re-embed at deploy |
| Q7, limit strip | The answer port returns `AnswerRefusedDTO(limit_reached)`; `SearchResults.answerLimitReached` is new; the card says "You have used today’s AI answers. Your matching records are below." Unit tests for the adapter, the service and `SearchCards`. Design change record 2026-10-02 |
| Tests | Backend 540 pass with `REMINDER_EMAIL_ENABLED=false` and no worker, after applying 007's migrations 0037 and 0038 to Supabase and deleting two leftover `@rls-test.invalid` users. `test_lists_and_lookup_stay_fast_at_a_thousand_memories` missed once at 1.18s and passed on rerun: network to Supabase. Frontend 328 pass, `tsc` and `oxlint` clean |
| Browser | API and worker restarted on D-22 and Q7. `/search passport`: 4 records, the visa task by meaning alone. "kayak": the no-match state. The limit strip needs the day's answers spent, so it rests on its unit tests |

The 14 records seeded for the artboard comparison are still in the user's account.

| # | Planned | Actual | Why | Approved by |
|---|---|---|---|---|
| D-23 | Build plan §5: `ANSWER_INSTRUCTION` | One sentence added: "State only what the records say; never add a year, date or detail they do not contain." | The wedding answer added a year its record lacks (Answer citations to judge) | user, 2026-10-02 |

After D-23, `test_search_answer_eval_live.py` passed 4 of 5 runs; the wedding answer said "February" with no year in every run printed. The one failure printed no assertion detail.

### Questions for the user

| # | Question | Blocks | Answer |
|---|---|---|---|
| ~~Q3~~ | NFR-7: (a) embed records and queries with separate task types, then rerun (Recommended); (b) set `MEANING_MAX_DISTANCE` to 0.48 and accept noise; (c) lower NFR-7's target | T-1.13 | **Answered 2026-10-02.** (b), 0.48. Set in `search/constants.py`; C-15 passes |
| ~~Q4~~ | Set `RELATED_MAX_DISTANCE` to 0.35? (a) yes, accepting the pairs above (Recommended); (b) keep 0.30 | T-3.9 | **Answered 2026-10-02.** (b), keep 0.30 |
| ~~Q5~~ | NFR-4's question latency: (a) rerun alone against Supabase, then profile the slower half (Recommended); (b) accept the miss for V1 | T-2.9 | **Answered 2026-10-02.** (b), accepted for V1 |
| ~~Q6~~ | The 0.48 noise: (a) embed records and queries with separate task types, re-embed, rerun C-15 and pick a tighter cutoff (Recommended); (b) keep 0.48 and change the design to match; (c) lower NFR-7's target and go back toward 0.35 | `SearchPassport`, FR-10 | **Answered 2026-10-02.** (a). D-22; cutoffs 0.40 and 0.20 |
| ~~Q7~~ | The daily-limit refusal copy: (a) give the limit its own strip, "You have used today's AI answers. Your matching records are below." (Recommended); (b) keep the unavailable strip for both | `SearchDegraded` | **Answered 2026-10-02.** (a). Built |
| Q8 | The 14 artboard seed records in the user's account: (a) keep them as dev test data (Recommended); (b) delete them through the app | Nothing | Open |

## Remaining work

Shipped 2026-10-02 on the user's approval. Open after shipping:

| Item | Needs | Owner |
|---|---|---|
| Q8 | The user's answer | user |
