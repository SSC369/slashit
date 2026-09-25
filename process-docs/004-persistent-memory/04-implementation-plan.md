---
doc: implementation-plan
feature: 004-persistent-memory
title: Persistent Memory
stage: 4
status: approved
owner: user
created: 2026-09-25
updated: 2026-09-25
approved_on: 2026-09-25
supersedes: null
split: true
---

# Implementation Plan (LLD) — Persistent Memory

> **Approved** by @user on 2026-09-25. Locked — changes require a change record (§7).

Context: [PRD](./01-prd.md) · [Design](./02-design.md) · [Build plan](./03-build-plan.md)

No code is written before this index and a slice's own sub-plan are approved,
and every slice builds on epic 003 (build plan AD-10, amended 2026-09-25: 003
is merged into this feature's branch rather than waited for on `main`).

Tables this feature touches, by migration:

| Table | New or changed | Migration | Slice |
|---|---|---|---|
| extension `vector` | new | `0023_pgvector` | 1 |
| `memories` | new, with the tombstone check constraint | `0024_memories` | 1 |
| `capture_turns` | changed: `resulting_memory_id`, outcomes `memory_saved`, `memory_listed` | `0025_capture_memory` | 1 |
| `pending_captures` | changed: `missing_field` value `fact` | `0025_capture_memory` | 1 |
| `ai_usage` | changed: `operation` | `0026_usage_operation` | 1 |
| `events` | changed: six memory event types | `0027_memory_events` | 1 |
| `capture_turns` | changed: `forgotten_at`, `affected_count`, the scrub check constraint, outcome `memory_forgotten` | `0028_forget` | 2 |
| `pending_captures` | changed: `missing_field` value `memory_conflict`, `candidate_text`, `candidate_category`, `conflicting_memory_ids` | `0029_memory_conflicts` | 3 |
| `capture_turns` | changed: outcome `memory_conflict_resolved` | `0029_memory_conflicts` | 3 |

The build plan's §3 named five migrations. They are split here by slice, so
each slice migrates only what it uses. The schema is unchanged.

## 1. Scope recap

Everything in the approved PRD ships, in three slices. Slice 1 saves, lists,
looks up, shows and edits memories, with categories and the secret caution.
Slice 2 adds forget, from Records and by command, with the history scrub. Slice
3 adds the conflict check and the "which is correct?" question, whose "Keep the
new one" answer forgets through slice 2. Order swapped 2026-09-25, see the
change log.

Slice 1 alone never ships to users. FR-10 says nothing saves without a conflict
check, so all three slices go out together. Slice 1 is still verifiable end to
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
| 1 | [04.1-save-and-browse.md](./04.1-save-and-browse.md) | `/remember` and `/add-memory` save with a category and a vector; `/memories` lists and looks up by word; Memories tab, All tab, detail and edit work, with every drawn state; the secret caution shows | 003 merged | approved 2026-09-25; built 2026-09-25, T-1.1, T-1.11, T-1.14 owed |
| 2 | [04.2-forget.md](./04.2-forget.md) | Forget from detail, by `/forget` with pick and confirm, and forget-all; history shows the placeholder; NFR-2's search-every-table test passes | 1 | draft |
| 3 | `04.3-conflicts.md` | A contradicting save asks which is correct; the three answers and "Decide later" work; "Keep the new one" forgets through slice 2; mobile conflict card | 1, 2 | not started |

Slice 3 depends on slice 2: its "Keep the new one" answer forgets the old
memory, and forget is slice 2's.

## 3. Shared file map

Only the files more than one slice changes. Each sub-plan lists its own.

| Path | Slice 1 | Slice 2 | Slice 3 |
|---|---|---|---|
| `backend/app/domains/memories/public.py` | created | adds forget | adds conflict types |
| `backend/app/domains/memories/services/memory_service.py` | created | adds tombstone | adds candidates and judgement |
| `backend/app/domains/capture/interactors/submit_capture.py` | three commands | `/forget` | conflict outcome |
| `backend/app/domains/capture/graphql/types.py` | memory union members | `ForgetCandidates`, `forgotten` | `MemoryConflictAsked` |
| `backend/app/core/deps.py` | memories wiring, gateway embed | scrub port | conflict resolver |
| `frontend/src/features/capture/components/MemoryCards.tsx` | saved, list, too long | forget cards | conflict card |
| `frontend/src/stores/MemoriesStore.ts` | created | forget | resolve |
| `frontend/src/constants/captureCommands.ts` | three commands | `/forget` | — |

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
passed through unmapped. Slice 2 adds `forget_memories(*, user_id, memory_ids)`
and `forget_all(*, user_id, expected_count)`. Slice 3 adds `MemoryConflictDTO`.

### The judgement call, slice 1 creates, slice 3 fills

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

Slice 1 sends no candidates, so `conflicting_ids` is always empty. Slice 3 sends
up to ten, each as `{id, text}`, and drops any returned id not in that list.
Descriptions stay terse: 001's dev log I-1 measured a long description doubling
latency.

### The scrub port, slice 2

```python
# memories/interfaces/ports.py — owned by memories, implemented by capture
class TurnScrubPort(Protocol):
    async def scrub_turns_for_memories(self, *, user_id: UUID, memory_ids: list[UUID]) -> int: ...
```

Called inside the forget transaction. It scrubs every turn whose
`resulting_memory_id` is in the list. That is enough for FR-23 because of one
rule slice 3 must keep: a conflict turn never stores an existing memory's text.
Its `question_text` is the fixed "Which is correct?", and the old memories are
shown from their live rows, by id, never copied.

### GraphQL, for the frontend

| Type or field | Slice |
|---|---|
| `Memory { id text category origin originalInput createdAt updatedAt }` | 1 |
| `MemoryCategory` enum, `MemorySaved { memory secretCaution }`, `MemoryList`, `MemoryTooLong { length limit }` | 1 |
| `memories(filter)`, `memory(id)`, `updateMemory` | 1 |
| `ForgetCandidates`, `forgetMemory`, `forgetFromCapture`, `CaptureTurn.forgotten` | 2 |
| `MemoryConflictAsked`, `resolveMemoryConflict`, `MemoryDiscarded` | 3 |

## 5. Rollout and flags

No flag. All three slices reach `main` together: slice 1 saves without a
conflict check, which FR-10 forbids in front of users, and slice 3 needs slice
2's forget. They are built and verified one at a time on this branch.

Migrations run forward only in production. Each has a working `downgrade` for
development.

## 6. Evaluation sets, before sub-plan approval

Build plan Q6 kept NFR-6 and NFR-7 and required labelled sets first.

| Set | Size | Owner | Needed by |
|---|---|---|---|
| Categories: fact and expected category, including uncategorisable facts | 60, `estimate` | Claude drafts, user corrects | End of slice 1. Drafted as its first task and corrected in parallel, per the user on 2026-09-25 |
| Conflicts: new fact, ten candidates, expected contradicting ids, a third of them true pairs such as two birthdays | 40, `estimate` | Claude drafts, user corrects | 4.3 approval |

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
| 2026-09-25 | Approved. Two amendments at approval: 003 is merged into this branch (AD-10 amended), and the category set is drafted as slice 1's first task and corrected in parallel instead of before approval | User approved and asked to proceed with dev | user |
| 2026-09-25 | Slices 2 and 3 swapped: 4.2 is now Forget, 4.3 Conflicts. Migrations renumbered to `0028_forget` and `0029_memory_conflicts`; `0028` also gains `capture_turns.affected_count` for "Forgot 2 memories". Rollout: all three slices ship together. The scrub port and forget contracts move from slice 3 to slice 2. Re-opened: none; neither sub-plan had been drafted | "Keep the new one" forgets the old memory, so conflicts cannot finish before forget exists. User chose the swap | user |
