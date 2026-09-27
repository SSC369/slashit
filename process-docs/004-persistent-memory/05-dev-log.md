---
doc: dev-log
feature: 004-persistent-memory
title: Persistent Memory
stage: 5
status: draft
owner: user
created: 2026-09-25
updated: 2026-09-27
approved_on: null
supersedes: null
---

# Dev Log — Persistent Memory

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-save-and-browse.md) · [04.2](./04.2-forget.md) · [04.3](./04.3-conflicts.md)

What actually happened. Deviations from the approved plan are recorded the day
they happen, per rule 5 of the root ruleset.

## Base

Epic 003 was merged into `claude/feature-004-planning-aevb3m` on 2026-09-25
(commit `aa092b0`), per build plan AD-10 as amended the same day. Before any 004
code: local PostgreSQL 16 with pgvector 0.6.0 and a stub Supabase `auth` schema,
all migrations to `0022` applied, **276 backend tests passing**, `mypy app` and
`ruff` clean. That is the baseline every number below compares against.

## Summary

All three slices are built and committed on `claude/feature-004-planning-aevb3m`.
The feature is **not shipped**: the checks that need the real model or a real
project are owed, listed in [Remaining work](#remaining-work).

| Slice | What a user can do | Code commit | Tests at the end of the slice |
|---|---|---|---|
| Base | Epic 003 merged in (AD-10, amended) | `aa092b0` | 276 backend |
| 1 Save and browse | `/remember` and `/add-memory` save a fact with a category and a vector; `/memories` lists and looks up by word; Memories tab, All tab, detail and edit; the secret caution | `14942ce` | 336 backend, 176 frontend |
| 2 Forget | Forget from the detail page, `/forget <words>` with pick and confirm, `/forget all` with a count guard; history keeps a placeholder and never the words | `2a21fad` | 358 backend, 192 frontend |
| 3 Conflicts | A contradicting save asks "Which is correct?": keep the new, keep the old, both, or decide later; the history scrub reaches the whole thread | `3ab8b2c` | 376 backend, 206 frontend |

Migrations `0023` to `0029` are applied locally and each has been downgraded
and upgraded again. Docs commits: `5d4623a`, `f633886`, `3e48f0f`, `7f58e04`,
`701b802`, `20a8e28`, `5f0b148`.

## Slice 1 — Save and browse

Backend and frontend built 2026-09-25. Verified against a real local
PostgreSQL 16 with pgvector, and in unit and component tests. The model is faked
at `LangChainGeminiProvider` in integration tests. **Not yet verified against
the real model or live in a browser**: see T-1.1, T-1.11 and T-1.14.

### Tasks

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|
| T-1.1 | 4.1 | Confirm the embedding model name and 768 dimensions | **owed** | No provider key and no route to Google from this environment. `gemini-embedding-001` is set as the default in `core/settings.py`, overridable by `GEMINI_EMBEDDING_MODEL`. The provider refuses any vector that is not 768 long, so a wrong model fails loudly as `ProviderUnavailable`, never silently |
| T-1.2 | 4.1 | Migrations `0023` to `0027` | **done** | Upgrade, downgrade to `0022` and upgrade again all clean. `\d memories` shows the forced RLS policy, both check constraints, the GIN index on `search_vector` |
| T-1.3 | 4.1 | Gateway `embed`, usage `operation`, allowance counting | **done** | C-11 in `test_embed_interactor.py`; the integration test sees one `generate` and one `embed` row per save |
| T-1.4 | 4.1 | Memories domain: model, repository, secret check, keyword query | **done** | C-7 (14 cases), C-8 unit and against PostgreSQL |
| T-1.5 | 4.1 | `MemoryService.save_memory` and the judgement adapter | **done** | C-2, C-4, C-5, C-6 in `test_save_memory.py` |
| T-1.6 | 4.1 | Capture: three commands, fact question, argument cap | **done** | C-1, C-3, C-4 in `test_memory_capture.py` |
| T-1.7 | 4.1 | Records-side interactors, GraphQL, reembed job | **done** | C-9, C-10 in `test_memory_interactors.py` and through GraphQL |
| T-1.8 | 4.1 | All tab through records' port | **done** | C-16 |
| T-1.9 | 4.1 | Log redaction by key | **done** | C-13, including the configured pipeline |
| T-1.10 | 4.1 | Boundary and load tests | **done** | C-12 (T7) through GraphQL. C-14: see Measurements |
| T-1.11 | 4.1 | Category evaluation set | **drafted, owed** | 60 cases in `backend/tests/eval/memory_categories.json`, status "draft, awaiting user correction". The live scorer `test_memory_eval_live.py` is written and type-checked but not run: no provider key here |
| T-1.12 | 4.1 | Frontend capture cards and commands | **done** | F-1, 7 cases in `MemoryCards.test.tsx`; SubmitCapture handler cases |
| T-1.13 | 4.1 | Frontend Memories tab, All rows, detail, edit | **done** | F-2 (6 cases), F-3 (4 cases), GetMemory and UpdateMemory handler cases |
| T-1.14 | 4.1 | Live browser pass against a real project | **owed** | No Supabase project credentials reachable from this environment, the same constraint 003's T-1.14 recorded. The canvas was not compared screen by screen against the running app |

### Checks

| Check | Result |
|---|---|
| `pytest -m "not live"` against local PostgreSQL 16 | **336 passed**, up from 276: 60 new |
| `mypy app` | clean, 265 files |
| `mypy tests` | 3 errors, all present before this slice (`test_settings.py` twice, `test_gateway_live.py` once) |
| `ruff check .` | clean |
| `npm run test` | **176 passed**, up from 148: 28 new |
| `npm run build` (`tsc -b` and Vite) | clean |
| `npm run lint` | one warning, present before this slice (`main.tsx`, unused `StrictMode`) |

### Measurements

| What | Result | Source |
|---|---|---|
| NFR-5, `memories` query plus a `/memories` lookup, 1,000 memories, 20 runs | **p95 472 ms per call**, target 1 s | `test_lists_and_lookup_stay_fast_at_a_thousand_memories`, local, in-process. A hosted database adds network time this cannot see |
| NFR-4, save latency | not measured | Needs the real model; owed with T-1.1 |
| NFR-6, category accuracy | not measured | Owed with T-1.11 |

### Deviations from the plan

| # | Planned | Actual | Why | Approved by |
|---|---|---|---|---|
| D-1 | Build plan §6: "A save is one transaction: memory insert and turn" | The memory commits first; the capture turn is written after it, and a turn failure is logged, never raised | Capture's standing rule since 001 (04.4 §9): the log never undoes the record. One transaction across two domains would need capture to own the memory's session | user, 2026-09-26 |
| D-2 | Index: `0024` carries "the tombstone check constraint" | Also `ck_memories_live_has_text`: a live row must have text | Without it a live row with NULL text would pass the tombstone check and render as an empty memory | user, 2026-09-26 |
| D-3 | Not stated | `vector` is created in the default schema, not Supabase's `extensions` schema | The type and the `<=>` operator then resolve unqualified on Supabase and locally alike. Supabase's advisor may flag it; moving it is one migration | user, 2026-09-26 |
| D-4 | 4.1 §4: "a 600-character outer guard on the whole line" | 1,000 | 600 would turn a 612-character fact, the design's own example, into a client error instead of FR-4's drawn state | user, 2026-09-26 |
| D-5 | 4.1 §4 | `EMBED_TIMEOUT_SECONDS = 3.0` in gateway constants | The plan named no embed budget. 3 s is `estimate`, inside NFR-4's 8 s | user, 2026-09-26 |
| D-6 | 4.1 §4 names `test_memories_boundary.py` and four fake files | Boundary cases live in `test_memories_graphql.py`; fakes are `fake_memory_port.py` and `fake_memory_repository.py` | One fixture set serves both, as 003's D-9 did | user, 2026-09-26 |
| D-7 | Design `MemoriesStates`, `MemoryDetail` | The detail has Edit only; Forget arrives with slice 3. Memory list states reuse 003's `ReminderListNotice` component | Forget is 4.3's scope. The notice component is generic apart from its name | user, 2026-09-26 |
| D-8 | Records tabs | The "More types arrive with later epics" hint beside the tabs is removed | The design's `RecordsMemories` draws four tabs and no hint | user, 2026-09-26 |

### Incidents and defects

| Date | What broke | Cause | Fix |
|---|---|---|---|
| 2026-09-25 | Migration `0024` failed on first run | The tombstone check named `embedding` before the column was added by raw SQL | Constraint created after the column, with `op.create_check_constraint` |
| 2026-09-25 | A 16-digit Luhn-invalid number was flagged as an ID number | The 12-digit pattern matched the first twelve digits of a longer grouped number | Pattern now requires the twelve digits to stand alone |

## Slice 2 — Forget

Backend and frontend built 2026-09-25 on slice 1 (`14942ce`). Verified against
local PostgreSQL 16 with `0028_forget` applied, and in unit and component
tests. Forget never calls the model, so nothing here waits on a provider key.
**Not yet seen live in a browser**: see T-2.11.

### Tasks

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|
| T-2.1 | 4.2 | Migration `0028_forget` | **done** | Upgrade, downgrade to `0027` and upgrade again clean. The scrub check refuses a row with `forgotten_at` set and text left in it |
| T-2.2 | 4.2 | Repository: tombstone, live ids, counts, term count | **done** | C-2.1, C-2.2 in `test_forget_graphql.py` |
| T-2.3 | 4.2 | `CaptureTurnScrubber` and turn repository changes | **done** | C-2.3. The scrubber lives in capture and imports nothing from memories; `test_layering.py` passes |
| T-2.4 | 4.2 | `MemoryService` forget, candidates, forget-all | **done** | C-2.4 to C-2.7 and C-2.11 in `test_forget.py` |
| T-2.5 | 4.2 | Capture `/forget` branch and `ConfirmForgetInteractor` | **done** | C-2.8 in `test_forget_capture.py` |
| T-2.6 | 4.2 | GraphQL: `forgetMemory`, `forgetFromCapture`, `ForgetCandidates`, turn fields | **done** | C-2.10 through GraphQL, user B against user A |
| T-2.7 | 4.2 | NFR-2 search-every-table test, AD-9 checks | **done** | C-2.9 reads every text column of every public table through `information_schema` after a forget and finds nothing. C-2.12 runs with the gateway switched off |
| T-2.8 | 4.2 | Frontend operations, stores, codegen | **done** | F-2.4: 7 handler cases across `ForgetMemory`, `ForgetFromCapture` and `SubmitCapture` |
| T-2.9 | 4.2 | Frontend forget cards and controller | **done** | F-2.1: 4 cases in `CommandCenterController.test.tsx`: pick, continue, confirm; cancel; no match and bare `/forget`; forget-all with a changed count |
| T-2.10 | 4.2 | Frontend detail Forget and history rows | **done** | F-2.2: 3 cases in `MemoryDetailController.test.tsx`. F-2.3: 1 case in `HistoryPanel.test.tsx` |
| T-2.11 | 4.2 | Live browser pass | **owed** | Same constraint as T-1.14: no Supabase project reachable from this environment |

### Checks

| Check | Result |
|---|---|
| `pytest -m "not live"` against local PostgreSQL 16 | **358 passed**, up from 336: 22 new |
| `mypy app` | clean, 269 files |
| `ruff check .` | clean |
| `npm run test` | **192 passed**, up from 176: 16 new |
| `npm run build` (`tsc -b` and Vite) | clean |
| `npm run lint` | one warning, present before slice 1 (`main.tsx`, unused `StrictMode`) |

### Deviations from the plan

| # | Planned | Actual | Why | Approved by |
|---|---|---|---|---|
| D-9 | 4.2 §5: `forgetFromCapture` returns `... \| MemoryNotFound` | Returns `... \| ForgetTargetGone`, a capture-owned type | The card's case is "already forgotten elsewhere", not a lookup miss, and capture's union keeps its own members | user, 2026-09-26 |
| D-10 | 4.2 §5: `ForgetCandidates` has no search text | It carries `searchText`; the frontend reads it as `forgetText` | The no-match card quotes the words. The alias is needed because `MemoriesListed.searchText` is nullable and codegen refuses one field name with two types in one selection | user, 2026-09-26 |
| D-11 | 4.2 §6: the unconfirmed `/forget` step not stated | Offering candidates writes no capture turn | Only a confirmed forget is history. Writing the offer would store the words typed, which FR-28 forbids | user, 2026-09-26 |
| D-12 | Design §4: "Memories with a 'Memory forgotten' note" | The note is the app's toast, with the design's copy. `Toast` now omits its link when `linkLabel` is empty | The toast is the app's one success note; a forget has nothing to open | user, 2026-09-26 |
| D-13 | Not stated | On the detail page, `MemoryNotFound` from `forgetMemory` is treated as forgotten | The memory was already forgotten from another tab; the user gets the outcome they asked for | user, 2026-09-26 |
| D-14 | 4.2 §4: `RecordsStore` drops forgotten rows | `RecordsStore` is unchanged | The All tab reads memories through `MemoriesStore`, so `removeMany` drops them there already | user, 2026-09-26 |

Slice 1's D-7 said Forget arrives with slice 3. It arrived with slice 2 after
the reorder, and the detail page now has it.

## Slice 3 — Conflicts

Backend and frontend built 2026-09-27 on slices 1 and 2. Verified against
local PostgreSQL 16 with `0029_memory_conflicts` applied, and in unit and
component tests, with the model faked. **Not yet verified against the real
model or live in a browser**: see T-3.10 and T-3.11. With this slice all three
are built; the feature ships once the owed live checks pass.

### Tasks

| # | Sub-plan | Task | Status | Note |
|---|---|---|---|---|
| T-3.1 | 4.3 | Conflict eval set | **done** | 40 cases in `backend/tests/eval/memory_conflicts.json`, accepted by the user without changes on 2026-09-27 |
| T-3.2 | 4.3 | Migration `0029_memory_conflicts` | **done** | Upgrade, downgrade to `0028` and upgrade again clean. The check refuses a row with a candidate and no ids |
| T-3.3 | 4.3 | `find_nearest` and candidates in `save_memory` | **done** | C-3.1, C-3.2 in `test_memory_conflicts.py` |
| T-3.4 | 4.3 | `resolve_conflict` and `save_resolved` | **done** | C-3.3, C-3.4, C-3.7, C-3.12 |
| T-3.5 | 4.3 | Capture: pending conflict, answer path, resolver | **done** | C-3.5, C-3.8, C-3.11 in `test_conflict_capture.py` |
| T-3.6 | 4.3 | Thread-wide scrub | **done** | C-3.6 unit and through GraphQL; after "Both are correct" and a forget, "Qatar" is found in no table |
| T-3.7 | 4.3 | GraphQL and boundary tests | **done** | C-3.9, C-3.10 in `test_conflicts_graphql.py` |
| T-3.8 | 4.3 | Frontend operation, store, conflict card, pill | **done** | F-3.1 to F-3.4: `ConflictCard.test.tsx` (5), controller (4), handlers (3 files) |
| T-3.9 | 4.3 | Live eval scorer | **done** | `test_memory_conflict_eval_live.py`, type-checked, marked `live` |
| T-3.10 | 4.3 | NFR-4 and NFR-7 on the real model | **owed** | No provider key here, the same constraint as T-1.1 and T-1.11 |
| T-3.11 | 4.3 | Live browser pass | **owed** | With T-1.14 and T-2.11. F-3.4's 390 px layout is checked by class names only until then |

### Checks

| Check | Result |
|---|---|
| `pytest -m "not live"` against local PostgreSQL 16 | **376 passed**, up from 358: 18 new |
| `mypy app` | clean, 271 files |
| `mypy tests` | 3 errors, the same three present before slice 1 |
| `ruff check .` | clean |
| `npm run test` | **206 passed**, up from 192: 14 new |
| `npm run build` (`tsc -b` and Vite) | clean |
| `npm run lint` | one warning, present before slice 1 (`main.tsx`) |

### Deviations from the plan

| # | Planned | Actual | Why | Approved by |
|---|---|---|---|---|
| D-15 | 4.3 §4: new `CONFLICT_CANDIDATE_LIMIT = 10` | Slice 1's `CANDIDATE_LIMIT = 10` is used | The same constant already existed for AD-5; a second would drift | logged, pending user |
| D-16 | 4.3 §4: `MemoryPort.list_live` so the card reads old memories live | The card reads them from the client's `MemoriesStore`. An edit or forget in this tab shows at once; one in another tab shows only when answered, where the server forgets only live ids | Q2 made waiting questions session-only, so the store already holds every memory the card shows. The port method was written, found unused, and removed | logged, pending user |
| D-17 | 0029: "a check that a conflict row carries all three" | The check ties `candidate_text` and a non-empty `conflicting_memory_ids` together. `candidate_category` may be NULL | An uncategorised fact is valid (FR-6), so a conflict row can have no category | logged, pending user |
| D-18 | Not stated | `answerPendingCapture` refuses a conflict row as not found | A conflict is answered by choice through `resolveMemoryConflict`, never by typed text | logged, pending user |
| D-19 | 4.3 §5: the scrub reaches the conflict thread | It reaches every thread, so a "What should Slashit remember?" question turn is blanked with the answer it led to. 4.2's C-2.3 test now expects three scrubbed turns, not two | One rule, keyed on the pending id, rather than a conflict-only special case. The extra turn held no fact | logged, pending user |
| D-20 | Design §4: success copy "Memory saved" | After "Keep the new one" the card reads "Memory saved · forgot 1 old memory" | FR-12 makes the forget part of the answer; the count confirms it happened | logged, pending user |
| D-21 | Design `Main`: "Decide later" | It folds the card to one line with "Answer now"; the waiting pill still counts it | The design draws the button, not the state after it | logged, pending user |

### Incidents and defects

| Date | What broke | Cause | Fix |
|---|---|---|---|
| 2026-09-27 | `test_tab_detail_edit_and_all_records` failed after candidates were added | The test's fake model chose a category from the whole prompt, which now includes candidate text | The fake reads only the prompt's first line, the fact |

## Remaining work

Everything below is owed before `index.md` can show 004 as shipped (index §7).
Nothing here can run in this environment: there is no model provider key, no
route to Google, and no Supabase project.

### Tasks owed

| # | Task | Blocked on | Owner | Done when |
|---|---|---|---|---|
| T-1.1 | Confirm the embedding model name and 768 dimensions | A Gemini key | Claude, with the key | One real save stores a 768-long vector; `GEMINI_EMBEDDING_MODEL` set or the default confirmed in `tech-stack.md` |
| T-1.11 | Correct the 60-case category set, then score it | The user's review; then a key | User, then Claude | `memory_categories.json` status "corrected"; accuracy over 85% (NFR-6) recorded here |
| T-3.10 | Score the conflict set; measure save latency | A key | Claude | NFR-7 and NFR-4 results recorded here |
| T-1.14, T-2.11, T-3.11 | Live browser pass of every state, against the canvas | A Supabase project and a key | Claude, with the user | The checklist below is complete, each row passed or raised as a change record |
| Approvals | Deviations D-15 to D-21 | The user | User | Each row reads "user" |
| Launch | The backup window in the forget line | The user, at launch (deferred 2026-09-25) | User | `BACKUP_LINE` in `memoryConstants.ts` names the real period |

### Live tests to run

Run from `backend/` with a real `GEMINI_API_KEY` in `.env` and the database
migrated. Both spend a fraction of a cent per case and never run in CI.

```
pytest -m live tests/integration/test_memory_eval_live.py -s          # NFR-6, T-1.11
pytest -m live tests/integration/test_memory_conflict_eval_live.py -s # NFR-7, T-3.10
```

| Measure | Target | Result so far |
|---|---|---|
| NFR-1, isolation | Zero cross-user reads | **Met in tests**: boundary cases for read, edit, lookup, forget, conflict candidates and answers |
| NFR-2, nothing left after forget | Zero matches | **Met in tests**: every text column of every table searched after a forget, and after a conflict thread is forgotten |
| NFR-3, no memory text in logs or events | Zero occurrences | **Met in tests**: the redaction test covers `text`, `fact`, `input_text`, `original_input`, `candidate_text`, `prompt` |
| NFR-4, save latency | Under 8 s at p95, 1,000 memories | **Not measured**: needs the real model. Time 20 saves against a user seeded with 1,000 memories |
| NFR-5, list and lookup | Under 1 s at p95, 1,000 memories | **472 ms** locally, in process. Re-measure against the hosted database |
| NFR-6, categories | Over 85% correct | **Not measured**: T-1.11 |
| NFR-7, conflicts | Catch over 80%; flag under 10% of other pairs; at most 1 of 19 traps | **Not measured**: T-3.10 |

### Browser pass checklist

Each row is one artboard in `assets/canvas/`, compared screen by screen with the
running app, in light and dark, desktop and 390 px where the canvas draws it.

| Area | Artboards | What to do |
|---|---|---|
| Save | `MemorySaved`, `MemorySecretCaution`, `CaptureStates` | `/remember` a fact, one with a card number, one over 500 characters, one with no fact, and one with the model switched off |
| Look up | `MemoriesLookup` | `/memories`, `/memories passport`, `/memories visa` with no match |
| Conflict | `Main`, `MobileConflict`, `DarkMemoryConflict`, `DarkMobileConflict` | Save "Preferred airline is Emirates", then "My preferred airline is Qatar Airways"; try each answer, "Decide later" and the waiting pill; forget the old memory in Records while the question waits |
| Forget by command | `ForgetPick`, `ForgetConfirm`, `ForgetAll` | `/forget airline` with one and with several matches, `/forget visa`, bare `/forget`, `/forget all` twice across two tabs |
| History | `HistoryForgotten` | After a forget, the placeholder row and "Forgot 1 memory" |
| Records | `RecordsMemories`, `RecordsAll`, `MemoriesStates`, `MobileMemories`, `DarkRecordsMemories` | Filters, empty, loading, error, signed out, filtered empty |
| Detail | `MemoryDetail`, `MemoryEdit`, `ForgetDetailConfirm`, `MobileMemoryDetail`, `DarkMemoryDetail`, `DarkForgetDetailConfirm` | Edit, over-long edit, forget, forget with the network off |

### Tests not yet written

| Gap | Why it matters | Where it would go |
|---|---|---|
| NFR-4 timing harness at 1,000 memories | The live scorers check accuracy, not latency | A `live` test beside the eval scorers |
| A component test of the waiting pill after "Decide later" on a 001 question | The pill counts both kinds; only the conflict kind is tested | `CommandCenterController.test.tsx` |
| An end-to-end browser test | Everything above is unit, component or API level | Needs the browser pass first |

## Deferred

| Item | Why deferred | Where it goes next |
|---|---|---|
| Backup window in the forget copy | User deferred it to launch, 2026-09-25 | Before launch |

## Notes for the next feature

- **N-1. Two root fields in one GraphQL request fail.** Fields in one request
  share `context.session` and resolve concurrently, so the second
  `user_transaction` raises "A transaction is already begun on this Session".
  Present before 004 and not caused by it; the frontend always sends one root
  field per request, which is why it has not surfaced. Found while writing
  `test_memories_graphql.py`. Worth a fix in `core/context.py` or `db.py` before
  anything batches queries.
- `ruff format --check .` reports six files it would reformat, the same six as
  before this slice. Only files this slice touched were formatted.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-25 | Created with slice 1's record | Slice 1 built | pending |
| 2026-09-25 | Slice 2's record added; Deferred table corrected for the slice reorder | Slice 2 built | pending |
| 2026-09-26 | Deviations D-1 to D-14 approved | User approved all | user |
| 2026-09-27 | Slice 3's record added | Slice 3 built | pending |
| 2026-09-27 | Summary and Remaining work added: owed tasks, live test commands, NFR status, browser checklist, test gaps | User asked for everything done and everything pending in one place | pending |
