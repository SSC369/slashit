---
doc: implementation-plan
feature: 004-persistent-memory
title: Persistent Memory
stage: 4
status: draft
owner: user
created: 2026-09-25
updated: 2026-09-25
approved_on: null
supersedes: null
split: true
---

# Implementation Plan (LLD) — Persistent Memory

Context: [PRD](./01-prd.md) · [Design](./02-design.md) · [Build plan](./03-build-plan.md)

No code is written before this index and a slice's own sub-plan are approved,
and no slice starts before epic 003 is merged to `main` (build plan AD-10).
Every path below is on `main` after that merge.

Tables this feature touches, by migration:

| Table | New or changed | Migration | Slice |
|---|---|---|---|
| extension `vector` | new | `0023_pgvector` | 1 |
| `memories` | new, with the tombstone check constraint | `0024_memories` | 1 |
| `capture_turns` | changed: `resulting_memory_id`, outcomes `memory_saved`, `memory_listed` | `0025_capture_memory` | 1 |
| `pending_captures` | changed: `missing_field` value `fact` | `0025_capture_memory` | 1 |
| `ai_usage` | changed: `operation` | `0026_usage_operation` | 1 |
| `events` | changed: six memory event types | `0027_memory_events` | 1 |
| `pending_captures` | changed: `missing_field` value `memory_conflict`, `candidate_text`, `candidate_category`, `conflicting_memory_ids` | `0028_memory_conflicts` | 2 |
| `capture_turns` | changed: outcome `memory_conflict_resolved` | `0028_memory_conflicts` | 2 |
| `capture_turns` | changed: `forgotten_at`, the scrub check constraint, outcome `memory_forgotten` | `0029_forget` | 3 |

The build plan's §3 named five migrations. They are split here by slice, so
each slice migrates only what it uses. The schema is unchanged.

## 1. Scope recap

Everything in the approved PRD ships, in three slices. Slice 1 saves, lists,
looks up, shows and edits memories, with categories and the secret caution.
Slice 2 adds the conflict check and the "which is correct?" question. Slice 3
adds forget, from Records and by command, with the history scrub.

Slice 1 alone never ships to users. FR-10 says nothing saves without a conflict
check, so slices 1 and 2 go out together. Slice 1 is still verifiable end to
end on its own, which is what the split needs.

## 2. Split decision

| Trigger | Threshold | This feature |
|---|---|---|
| Tasks in the breakdown | more than 15 | about 45, `estimate` |
| Files created or modified | more than 25 | about 90, `estimate` |
| Independently shippable slices | more than one | three |
| Distinct boundaries touched | more than two | five: capture, memories, gateway, records, analytics, plus the worker |
| Length of the drafted plan | more than 500 lines | over, as one document |

**Decision:** split into three sub-plans. Sub-plans 2 and 3 are drafted as the
slice before each lands, as 003 did.

### Slices

| # | Sub-plan | What works when it lands | Depends on | Status |
|---|---|---|---|---|
| 1 | [04.1-save-and-browse.md](./04.1-save-and-browse.md) | `/remember` and `/add-memory` save with a category and a vector; `/memories` lists and looks up by word; Memories tab, All tab, detail and edit work, with every drawn state; the secret caution shows | 003 merged | draft |
| 2 | `04.2-conflicts.md` | A contradicting save asks which is correct; the three answers and "Decide later" work; mobile conflict card | 1 | not started |
| 3 | `04.3-forget.md` | Forget from detail, by `/forget` with pick and confirm, and forget-all; history shows the placeholder; NFR-2's search-every-table test passes | 1 | not started |

Slices 2 and 3 are independent of each other. Slice 3 touches the pending
conflict only to drop forgotten ids from it, so whichever lands second adds
that one line.

## 3. Shared file map

Only the files more than one slice changes. Each sub-plan lists its own.

| Path | Slice 1 | Slice 2 | Slice 3 |
|---|---|---|---|
| `backend/app/domains/memories/public.py` | created | adds conflict types | adds forget |
| `backend/app/domains/memories/services/memory_service.py` | created | adds candidates and judgement | adds tombstone |
| `backend/app/domains/capture/interactors/submit_capture.py` | three commands | conflict outcome | `/forget` |
| `backend/app/domains/capture/graphql/types.py` | memory union members | `MemoryConflictAsked` | `ForgetCandidates`, `forgotten` |
| `backend/app/core/deps.py` | memories wiring, gateway embed | conflict resolver | scrub port |
| `frontend/src/features/capture/components/MemoryCards.tsx` | saved, list, too long | conflict card | forget cards |
| `frontend/src/stores/MemoriesStore.ts` | created | resolve | forget |
| `frontend/src/constants/captureCommands.ts` | three commands | — | `/forget` |

## 4. Interfaces and contracts

Only what crosses a slice or domain boundary. Python signatures are
keyword-only, per `backend/.claude/rules/code-rules.md`.

### Gateway embed, slice 1

```python
# gateway/public.py
@dataclass(frozen=True)
class Embedding:
    vector: tuple[float, ...]   # length EMBEDDING_DIMENSIONS, 768
    model: str

EmbedResult = Embedding | ProviderUnavailable | ProviderTimeout | SharedQuotaExhausted
EmbedInteractor.embed(*, user_id: UUID, text: str) -> EmbedResult
# Writes one ai_usage row, operation="embed". Never consults the per-user cap (T9).
```

`UserLimitReached` is not a member: an embed cannot be refused on the cap.
`AllowanceService` counts `operation = 'generate'` rows only.

### Memories published service, slice 1

```python
# memories/public.py
class MemoryCategory(StrEnum): PERSONAL, PEOPLE, PROFESSIONAL, LIFE

@dataclass(frozen=True)
class MemoryDTO:
    id: UUID; user_id: UUID; text: str; category: MemoryCategory | None
    origin: Literal["command", "edit"]; original_input: str
    created_at: datetime; updated_at: datetime

@dataclass(frozen=True)
class MemorySavedDTO:
    memory: MemoryDTO
    secret_caution: SecretKind | None   # CARD, ID_NUMBER, TAX_ID, CREDENTIAL

MemoryService.save_memory(*, user_id, text, original_input) -> SaveOutcome
MemoryService.list_memories(*, user_id, category: MemoryCategory | None | Uncategorised,
                            search: str | None) -> list[MemoryDTO]
MemoryService.lookup(*, user_id, text: str) -> list[MemoryDTO]   # FR-20 ranking
MemoryService.count(*, user_id) -> int
```

`SaveOutcome` in slice 1 is `MemorySavedDTO` or a gateway failure member,
passed through unmapped. Slice 2 adds `MemoryConflictDTO`. Slice 3 adds
`forget(*, user_id, memory_ids)` and `forget_all(*, user_id, expected_count)`.

### The judgement call, slice 1 creates, slice 2 fills

```python
MEMORY_JUDGEMENT_SCHEMA = {
  "type": "object",
  "properties": {
    "category": {"type": "string", "enum": ["personal","people","professional","life","none"]},
    "conflicting_ids": {"type": "array", "items": {"type": "string"}},
  },
  "required": ["category", "conflicting_ids"],
}
```

Slice 1 sends no candidates, so `conflicting_ids` is always empty. Slice 2 sends
up to ten, each as `{id, text}`, and drops any returned id not in that list.
Descriptions stay terse: 001's dev log I-1 measured a long description doubling
latency.

### The scrub port, slice 3

```python
# memories/interfaces/ports.py — owned by memories, implemented by capture
class TurnScrubPort(Protocol):
    async def scrub_turns_for_memories(self, *, user_id: UUID, memory_ids: list[UUID]) -> int: ...
```

Called inside the forget transaction. It scrubs every turn whose
`resulting_memory_id` is in the list. That is enough for FR-23 because of one
rule slice 2 must keep: a conflict turn never stores an existing memory's text.
Its `question_text` is the fixed "Which is correct?", and the old memories are
shown from their live rows, by id, never copied.

### GraphQL, for the frontend

| Type or field | Slice |
|---|---|
| `Memory { id text category origin originalInput createdAt updatedAt }` | 1 |
| `MemoryCategory` enum, `MemorySaved { memory secretCaution }`, `MemoryList`, `MemoryTooLong { length limit }` | 1 |
| `memories(filter)`, `memory(id)`, `updateMemory` | 1 |
| `MemoryConflictAsked`, `resolveMemoryConflict`, `MemoryDiscarded` | 2 |
| `ForgetCandidates`, `forgetMemory`, `forgetAllMemories`, `CaptureTurn.forgotten` | 3 |

## 5. Rollout and flags

No flag. Slices 1 and 2 merge to `main` together, or slice 1 lands with the
three commands hidden from command discovery until slice 2 follows. The first
is simpler and is the plan. Slice 3 may follow separately: without it, a memory
cannot be forgotten, which PRD FR-21 needs before real users arrive.

Migrations run forward only in production. Each has a working `downgrade` for
development.

## 6. Evaluation sets, before sub-plan approval

Build plan Q6 kept NFR-6 and NFR-7 and required labelled sets first.

| Set | Size | Owner | Needed by |
|---|---|---|---|
| Categories: fact and expected category, including uncategorisable facts | 60, `estimate` | Claude drafts, user corrects | 4.1 approval |
| Conflicts: new fact, ten candidates, expected contradicting ids, a third of them true pairs such as two birthdays | 40, `estimate` | Claude drafts, user corrects | 4.2 approval |

Both live in `backend/tests/eval/` as JSON and run as a live test, marked like
`test_capture_live.py`, never in CI.

## 7. Definition of done, for the feature

- Every task in 04.1 to 04.3 is shipped or explicitly dropped in the dev log.
- NFR-1: T7 boundary tests pass for read, edit, lookup, conflict candidate and
  forget.
- NFR-2: after a forget, the text is found in no table.
- NFR-3: the logging test passes with memory text in every logged field.
- NFR-4 to NFR-7 measured and recorded in the dev log, with the evaluation set
  results.
- The design matches the canvas, or a change record says why not.
- `index.md` shows 004 as shipped. The backup window is filled before launch.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-25 | Created as the index, with sub-plan 4.1 drafted | Build plan approved; user asked to proceed | pending |
