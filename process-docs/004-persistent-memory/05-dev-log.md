---
doc: dev-log
feature: 004-persistent-memory
title: Persistent Memory
stage: 5
status: draft
owner: user
created: 2026-09-25
updated: 2026-09-25
approved_on: null
supersedes: null
---

# Dev Log — Persistent Memory

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-save-and-browse.md) · [04.2](./04.2-forget.md)

What actually happened. Deviations from the approved plan are recorded the day
they happen, per rule 5 of the root ruleset.

## Base

Epic 003 was merged into `claude/feature-004-planning-aevb3m` on 2026-09-25
(commit `aa092b0`), per build plan AD-10 as amended the same day. Before any 004
code: local PostgreSQL 16 with pgvector 0.6.0 and a stub Supabase `auth` schema,
all migrations to `0022` applied, **276 backend tests passing**, `mypy app` and
`ruff` clean. That is the baseline every number below compares against.

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
| D-1 | Build plan §6: "A save is one transaction: memory insert and turn" | The memory commits first; the capture turn is written after it, and a turn failure is logged, never raised | Capture's standing rule since 001 (04.4 §9): the log never undoes the record. One transaction across two domains would need capture to own the memory's session | logged, pending user |
| D-2 | Index: `0024` carries "the tombstone check constraint" | Also `ck_memories_live_has_text`: a live row must have text | Without it a live row with NULL text would pass the tombstone check and render as an empty memory | logged, pending user |
| D-3 | Not stated | `vector` is created in the default schema, not Supabase's `extensions` schema | The type and the `<=>` operator then resolve unqualified on Supabase and locally alike. Supabase's advisor may flag it; moving it is one migration | logged, pending user |
| D-4 | 4.1 §4: "a 600-character outer guard on the whole line" | 1,000 | 600 would turn a 612-character fact, the design's own example, into a client error instead of FR-4's drawn state | logged, pending user |
| D-5 | 4.1 §4 | `EMBED_TIMEOUT_SECONDS = 3.0` in gateway constants | The plan named no embed budget. 3 s is `estimate`, inside NFR-4's 8 s | logged, pending user |
| D-6 | 4.1 §4 names `test_memories_boundary.py` and four fake files | Boundary cases live in `test_memories_graphql.py`; fakes are `fake_memory_port.py` and `fake_memory_repository.py` | One fixture set serves both, as 003's D-9 did | logged, pending user |
| D-7 | Design `MemoriesStates`, `MemoryDetail` | The detail has Edit only; Forget arrives with slice 3. Memory list states reuse 003's `ReminderListNotice` component | Forget is 4.3's scope. The notice component is generic apart from its name | logged, pending user |
| D-8 | Records tabs | The "More types arrive with later epics" hint beside the tabs is removed | The design's `RecordsMemories` draws four tabs and no hint | logged, pending user |

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
| D-9 | 4.2 §5: `forgetFromCapture` returns `... \| MemoryNotFound` | Returns `... \| ForgetTargetGone`, a capture-owned type | The card's case is "already forgotten elsewhere", not a lookup miss, and capture's union keeps its own members | logged, pending user |
| D-10 | 4.2 §5: `ForgetCandidates` has no search text | It carries `searchText`; the frontend reads it as `forgetText` | The no-match card quotes the words. The alias is needed because `MemoriesListed.searchText` is nullable and codegen refuses one field name with two types in one selection | logged, pending user |
| D-11 | 4.2 §6: the unconfirmed `/forget` step not stated | Offering candidates writes no capture turn | Only a confirmed forget is history. Writing the offer would store the words typed, which FR-28 forbids | logged, pending user |
| D-12 | Design §4: "Memories with a 'Memory forgotten' note" | The note is the app's toast, with the design's copy. `Toast` now omits its link when `linkLabel` is empty | The toast is the app's one success note; a forget has nothing to open | logged, pending user |
| D-13 | Not stated | On the detail page, `MemoryNotFound` from `forgetMemory` is treated as forgotten | The memory was already forgotten from another tab; the user gets the outcome they asked for | logged, pending user |
| D-14 | 4.2 §4: `RecordsStore` drops forgotten rows | `RecordsStore` is unchanged | The All tab reads memories through `MemoriesStore`, so `removeMany` drops them there already | logged, pending user |

Slice 1's D-7 said Forget arrives with slice 3. It arrived with slice 2 after
the reorder, and the detail page now has it.

## Deferred

| Item | Why deferred | Where it goes next |
|---|---|---|
| Conflict check (FR-10 to FR-14) | Slice 3, after the reorder | `04.3-conflicts.md`, not yet drafted |
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
