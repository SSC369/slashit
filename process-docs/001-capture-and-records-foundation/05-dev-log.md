---
doc: dev-log
feature: 001-capture-and-records-foundation
title: Capture and Records Foundation
stage: 5
status: draft
owner: user
created: 2026-09-13
updated: 2026-09-23
approved_on: null
supersedes: null
---

# Dev Log — Capture and Records Foundation

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-capture-core.md)

What actually happened. Deviations from the approved plan are recorded the day
they happen, per rule 5 of the root ruleset.

## Slice 1 — Capture Core

Backend and frontend both built and verified 2026-09-13, against the real
database, the real gateway, and a real signed-in Supabase user, in a browser.

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-1.a | `records`: `Task` model, `TaskDTO`/`Task` type, migration `0003_tasks` | **done** | Applied and reversed against the live database |
| T-1.b | `records`: `TaskRepository.create_task`, `RecordsService`, `public.py` | **done** | Extended beyond plan: `list_open_tasks_for_user`, see deviations |
| T-1.c | `capture`: `PendingCapture` model, migration `0004_pending_captures` | **done** | Applied and reversed against the live database |
| T-1.d | `capture`: `constants.py`, `interfaces/{dtos,repositories,ports}.py` | **done** | |
| T-1.e | `capture`: `SqlPendingCaptureRepository` | **done** | Against the request's own session, not a session factory — see deviations |
| T-1.f | `capture`: both adapters | **done** | Port renamed `TaskCreationPort` → `TaskPort`, extraction port generalised — see deviations |
| T-1.g | `capture`: `SubmitCaptureInteractor`, all nine outcomes | **done** | Returns DTOs, not GraphQL types — see deviations |
| T-1.h | `capture`: `AnswerPendingCaptureInteractor`, `DiscardPendingCaptureInteractor` | **done** | Answering a due-date question resolves the answer through the gateway too — see deviations |
| T-1.i | `capture`: `graphql/types.py`, `graphql/mutations.py`, `deps.py`, `schema.py` wiring | **done** | First mutation this project has; added the root `Mutation` type |
| T-1.j | `capture`: the live test | **done** | Passed after a schema fix, see incidents |
| T-1.k | Frontend: `tokens.css`, both modes | **done** | Values sourced from the canvas's `DarkTokens.dc.html`; an unplanned skeleton step came first, see deviations |
| T-1.l | Frontend: three operation folders | **done** | Apollo Client 4 needed a type-override file the plan did not anticipate, see deviations |
| T-1.m | Frontend: `CaptureStore` | **done** | |
| T-1.n | Frontend: `CommandCenterController` and components | **done** | Manual pass in a real browser reproduces every flow the canvas prototype proved: add-task with a date, add-task without one (pending question, answered), `/tasks`, non-command guidance, unrecognised command |

### Verification

| Check | Result |
|---|---|
| `pytest tests/unit` | **53 passed** |
| `pytest tests/integration -m "not live"` | **30 passed**, including the standing RLS guard (`test_every_user_table_is_locked_down`) covering the two new tables |
| `pytest tests/integration -m live` | **1 passed**, real `/add-task` call through the full stack: schema → auth → resolver → interactor → adapter → gateway → database |
| `ruff check .` / `ruff format --check .` | Clean |
| `mypy app` (strict) | No issues in 67 source files |
| `alembic upgrade head` then `downgrade 0002_ai_user_limit` then `upgrade head` | Both new migrations apply and reverse cleanly against the live database |
| `tsc -b --noEmit` | Clean |
| `oxlint` | Clean (generated files excluded, see D-21) |
| `npm run build` | Clean production build |
| Manual browser pass, real backend + real Gemini + a real Supabase session | `/add-task` with a date, `/add-task` without one → pending question → answered → task created, `/tasks` listing two real rows, a non-command with "Use with /add-task", an unrecognised command |

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-13 | The `CaptureResult` union is **nine** members, not the ten the build plan's heading said, and capture imports the gateway's five outcome types directly instead of mirroring them into its own `graphql/errors.py` | Reading the actual epic 000 code while building this slice: the gateway has no `graphql/` folder, so its types already cross legitimately via `public.py`. The build plan's reasoning was wrong, corrected there with a change record the same day | `03-build-plan.md` §7 corrected. No behaviour change |
| D-14 | `SubmitCaptureInteractor` and `AnswerPendingCaptureInteractor` return plain DTOs (`TaskDTO`, `list[TaskDTO]`, `PendingCaptureDTO`, `NonCommandGuidanceDTO`, `UnrecognisedCommandDTO`, or a gateway type), never a GraphQL type. The resolver in `graphql/mutations.py` converts | The sub-plan's own contract had the interactor importing from `capture/graphql/types.py`, which repo-rules.md section 7.3 forbids: an interactor imports nothing from `graphql/`. Caught before it shipped, not after | Matches the documented layer contract exactly. No sub-plan update needed since this is what "the resolver converts DTO to GraphQL type" already meant |
| D-15 | `SqlTaskRepository` and `SqlPendingCaptureRepository` take the request's own `AsyncSession` directly, not a `session_factory` | The sub-plan's contract copied the gateway's `SqlUsageRepository` shape, which exists specifically for AD-8 (a usage row must survive the caller's later work rolling back). Neither table here has that requirement, so the plain per-request session repo-rules.md section 7.4 documents is the correct, simpler choice | `Context` gained a `session_factory` field (see D-16), used only by the one collaborator that still needs an independent transaction: the gateway |
| D-16 | `Context` (`app/core/context.py`) gained a `session_factory: async_sessionmaker[AsyncSession]` field | Building the gateway from inside `capture`'s composition needs its own transaction (D-15's reasoning, in reverse); `Context` only carried a single shared `session` | Additive, no existing field changed. Every other domain keeps using `context.session` |
| D-17 | `TaskCreationPort` renamed `TaskPort` and gained `list_open_tasks`; `RecordsService`/`TaskRepository` gained `list_open_tasks(_for_user)` a slice early | The sub-plan scoped `TaskRepository` to `create_task` only, but its own test plan (T-1.9, `/tasks` lists open tasks) needs a read path that did not exist yet, and its own interactor contract listed a `task_repository: TaskRepository` parameter directly on `SubmitCaptureInteractor` — crossing into `records` without a port, which section 6 forbids. Resolved by extending the existing port/service rather than crossing directly | Slice 2 extends the same `TaskRepository` Protocol with detail, edit, complete and delete; it does not need to add listing, that already exists |
| D-18 | `AnswerPendingCaptureInteractor` takes an `ExtractionPort`, not just a `TaskPort`, and resolves a due-date answer ("Friday", "tomorrow") through the gateway with a second, minimal schema (`DUE_AT_ONLY_SCHEMA`) | Not designed in the sub-plan. A free-text date answer needs real resolution somewhere; the alternatives were a second date-parsing dependency (against T4's provider-boundary rule) or accepting ISO-only answers (breaking the demonstrated canvas prototype UX). Reusing the gateway, already the one place date resolution happens, was the smallest correct option | `ExtractionPort.extract` is generic (`schema`, `instruction` as parameters) rather than hardwired to the task schema, so both callers pass their own. One more gateway call, and one more possible `AnswerCouldNotBeUnderstoodError`, not in the original error table |
| D-19 | Backend gained a local-only CORS middleware in `app/main.py` (`allow_origins` limited to the Vite dev server, gated on `settings.environment == "local"`) | The frontend did not exist before this slice, so nothing in the backend previously needed to answer a browser request from a different origin. No production origin is configured; that is a deploy-time decision, not made here | Composition-root change only, no domain code touched. Needs revisiting once the frontend has a real deployed origin |
| D-20 | Frontend `package.json` sets `noUnusedLocals`/`noUnusedParameters` to `false` in `tsconfig.app.json`; `.oxlintrc.json` excludes `**/*.generated.ts` | `@graphql-codegen`'s `near-operation-file` preset always emits an `import * as Types` in every operation file, used or not, which `noUnusedLocals` flagged as an error in a file repo-rules.md forbids hand-editing. Generated output cannot satisfy a rule it doesn't control | Applies repo-wide, not just to generated files, since a single tsconfig covers `src/`. Hand-written dead code is now only caught by `oxlint`'s own unused-vars rule, which still runs on hand-written files |
| D-21 | `src/api/lib/apolloTypeOverrides.d.ts` pins Apollo Client 4.2's hook signature style to `"classic"`, alongside declaring `errorPolicy: "all"` in `DeclareDefaultOptions` | Apollo Client 4.2 requires a `DeclareDefaultOptions` module augmentation before a non-default `errorPolicy` in `defaultOptions` type-checks at all (repo-rules.md §4's mandated default), but declaring one also switches every hook to "modern" signatures, which reject the manually-specified `<Data, Variables>` generics `@graphql-codegen/typescript-react-apollo` v5 emits (it predates modern signatures and does not emit `TypedDocumentNode`). The Apollo changelog names this exact classic-pin combination for this migration state | A future `typescript-react-apollo` release that emits `TypedDocumentNode` should drop this file and the manual generics in every `useOperation.ts` |
| D-22 | `useSubmitCapture`/`useAnswerPendingCapture` gained an `onRequestFailed` callback, invoked both from the mutation's `onError` and when `onCompleted` fires with a null result field | Not in the sub-plan's hook contract. Found in manual testing: a top-level GraphQL error (hit once locally on an auth misconfiguration, see incidents) left its turn stuck showing "Reading your command" forever, since `errorPolicy: "all"` calls `onCompleted` with a null field rather than rejecting. `CommandCenterController` resolves the turn to the same `refused` status a `UserLimitReached`-style outcome uses | One more optional callback per submit-shaped hook; `responseHandler.ts`'s union switch is unchanged |
| D-23 | `CommandCenterController` scrolls its turn stream to the latest turn on every new turn (a `useRef` + `useEffect` keyed on `turns.length`) | The canvas prototype did this in `componentDidUpdate`; the first port of it to React was missed and only surfaced when a manual multi-turn browser pass left new turns below the fold | Matches the approved prototype's behaviour; no contract change |

### Incidents and defects

| # | What broke | Cause | Fix |
|---|---|---|---|
| I-1 | The live test (`T-1.13`) failed twice with `ProviderTimeout`, consistently around 10.3–10.7s against the 8s budget (NFR-2), even though gateway's own live test reliably completes in ~5.4s with a similar schema | A verbose `description` on the `due_at` JSON Schema property (two sentences) measurably slowed generation. Isolated by direct timing: gateway's exact schema/instruction ran in 5.3–5.5s twice; swapping in capture's schema alone (same field name, long description) reproduced the ~10.7s timeout; shortening the description to gateway's terse style brought it to 6.2s | `TASK_EXTRACTION_SCHEMA` and `DUE_AT_ONLY_SCHEMA` rewritten with terse, one-line descriptions matching gateway's own style; the adapter's appended reference-moment sentence shortened from two sentences to `"Today is {now_iso}."`. The live test then passed at 7.96–8.48s |
| I-2 | Even after the fix, one full-suite run (this test running back-to-back with gateway's own live test) still timed out; three isolated reruns passed at 7.96–8.48s | Real latency sits close enough to the 8s budget that ordinary variance can cross it. Not a code defect: the same request sometimes takes 6s, sometimes just over 8s | Not fixed further here — diminishing returns on shaving more schema text, and NFR-2's own docstring in `gateway/constants.py` already calls 8s an `estimate` to be revised against real p95 "once epic 001 calls this." That is now happening. **Flagged, not resolved**: revisit `PROVIDER_TIMEOUT_SECONDS` against a real measurement sample once more calls have been made, likely in slice 2 or 3. This is epic 000's constant; changing it needs a change record there, not here |
| I-3 | The first manual browser submission failed: the backend rejected the request as `Not authenticated`, logging `PyJWKClientConnectionError` while fetching Supabase's JWKS endpoint | The backend's Python venv (a python.org install under `/Library/Frameworks/Python.framework`) has no working default CA bundle; `ssl.get_default_verify_paths()` points at a `cert.pem` that install never wrote. `httpx` (used for the Gemini calls) ships its own certifi-backed default context and was unaffected; `PyJWKClient` uses stdlib `urllib`, which was not | Local machine fix, not a code change: the backend process needs `SSL_CERT_FILE` set to `certifi.where()`. This is a workstation setup gap, not tracked as a deviation because nothing in the repository changed; worth a line in a local setup doc if one gets written |
| I-4 | The stuck-loading turn from I-3's failed request never resolved, even after the fix, because it belonged to a promise whose callbacks were already bound before the code changed | Expected once traced: an in-flight mutation keeps the closures it started with. Not a bug in the final code, confirmed by every later submission resolving correctly | No fix needed; the page was reloaded, which cleared the (intentionally unpersisted) turn history |

### Not done, and why

No feature this epic has designed is skipped, but manual verification needed a
sign-in path that does not exist as product UI yet: no epic has designed a
sign-up or sign-in screen. `src/api/lib/supabaseClient.ts` exposes the
Supabase client on `window.__supabaseClient` in dev builds only
(`import.meta.env.DEV`), so a session can be established from the browser
console for manual testing. A real test account
(`sai9821c+slashitdev@gmail.com`) exists in the project's Supabase instance for
this purpose. This is a dev-only affordance, not a feature; a real sign-in
screen is an open gap this epic inherits rather than introduces, and belongs to
whichever epic is judged to own identity UI.

## Slice 2 — Records and Settings

Backend and frontend both built and verified 2026-09-13, against the real
database and a real browser session.

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-2.1 | `TaskRepository` Protocol extended; `task_repository.py` implements list/get/update/set_status/delete | **done** | |
| T-2.2 | `list_tasks.py`, `get_record_detail.py` interactors | **done** | |
| T-2.3 | `update_task.py`, `delete_tasks.py` interactors | **done** | `completeTask` reuses `UpdateTaskInteractor` rather than a fifth interactor — not itemised as its own row, matches the sub-plan's own interactor list |
| T-2.4 | `records/graphql/` — types, inputs, errors, queries, mutations | **done** | `Task` itself not redeclared here, see deviations |
| T-2.5 | `identity` domain, backend, in full | **done** | |
| T-2.6 | `deps.py` wiring, `schema.py` registration for both domains | **done** | |
| T-2.7 | Boundary tests, `tests/integration/` | **done** | Built as GraphQL-level tests (real JWTs), not raw-SQL boundary tests, since the union outcome (`RecordNotFound`) is what rule T7 needs proven here, not just row invisibility |
| T-2.8 | Frontend operation folders, all eight, plus `TaskFragment` | **done** | Query folders use `useLazyQuery` + a `useEffect` in the controller, not `onCompleted` — see deviations |
| T-2.9 | `RecordsStore`, `SettingsStore`, `RootStore` wiring | **done** | |
| T-2.10 | `RecordsController`, `RecordTable`, `EmptyRecords` | **done** | |
| T-2.11 | `RecordDetailController`, `RecordEditForm`, `DeleteConfirmModal` | **done** | Status is changed through the same "Save changes" as the title, per `RecordEdit.dc.html` — see deviations |
| T-2.12 | `SettingsController`, `detectTimezone.ts` | **done** | |
| T-2.13 | Response-handler tests for all four mutations | **done** | Vitest and React Testing Library newly installed for this slice; no frontend test infrastructure existed before it |

### Verification

| Check | Result |
|---|---|
| `pytest tests/unit` | **70 passed** (53 from slice 1 + 17 new) |
| `pytest tests/integration -m "not live"` | **46 passed** (30 from slice 1 + 16 new), including the standing RLS guard now covering `user_settings` automatically |
| `ruff check .` / `ruff format --check .` | Clean |
| `mypy app` (strict) | No issues in 99 source files |
| `alembic upgrade head` then `downgrade 0004_pending_captures` then `upgrade head` | `0005_user_settings` applies and reverses cleanly against the live database |
| `npx tsc -b --noEmit` / `npx oxlint` | Clean |
| `npm run test` (Vitest, newly installed this slice) | **17 passed**, response-handler exhaustiveness for `UpdateTask`, `CompleteTask`, `DeleteTask`, `UpdateTimezone`, plus `RecordsController`'s empty-state case |
| `npm run build` | Clean production build |
| Manual browser pass, real backend + real Supabase session | Records table listed all 3 real tasks; opened a detail page; edited a title and flipped status to Done via the segmented control, table updated live; deleted a task via the confirm modal; search filtered server-side; Settings showed the real detected browser timezone, changed it, confirmed it persisted after reload |
| D-43, due-date editing (2026-09-14) | `mypy --strict` / `ruff check` clean; `pytest` **126 passed** (was 124, +2: T-2.6a's set and clear cases). `npx tsc -b --noEmit` / `npx oxlint` / `npm run build` clean; `npm run test` **44 passed** (was 39, +5: two `RecordEditForm` cases, three `formatDate.test.ts` cases). Manual browser pass, real backend restarted for the schema change, real Supabase session: set a due date on a task that had none, saved, detail view showed it; cleared it back to no due date, saved, confirmed; hit I-9 live and fixed it in the same pass |

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-24 | `records/graphql/types.py` does not redeclare `Task` | The sub-plan's file table (section 4) listed `Task` as one of the types created there, drafted before slice 1 settled where `Task` actually lives: `interfaces/dtos.py`, placed there specifically so it can cross into `capture` (deviation D-13). Redeclaring it in `graphql/types.py` would give the schema two incompatible `Task` types | `graphql/types.py` holds only what slice 1 didn't already build: the `TaskStatus`, `RecordOrigin` and `SortField` enums. No contract change, since every consumer (capture, and now records' own resolvers) already imports `Task` from `interfaces/dtos.py` |
| D-25 | `records`' and `identity`'s `graphql/__init__.py` files are empty; `app/graphql/schema.py` composes `Query`/`Mutation` by multiple inheritance from each domain's `RecordQueries`/`RecordMutations`/`IdentityQueries`/`IdentityMutations` classes directly, the same way `CaptureMutations` already does | Matches the pattern slice 1 actually shipped (`capture/graphql/__init__.py` is empty; `schema.py` imports `CaptureMutations` directly), not repo-rules.md §11's aspirational "domains register `queries =`/`mutations =`, schema.py iterates a domain list" description, which was never implemented | None functionally; `schema.py`'s class-base list grows by one entry per domain, same cost as slice 1 |
| D-26 | Every resolver argument that would otherwise shadow a Python builtin (`id`, `filter`, `input`) is renamed to `id_`/`filter_`/`input_` in the function signature, with `Annotated[T, strawberry.argument(name="id")]` (etc.) preserving the external GraphQL field name | repo-rules.md §7.1's own worked example uses `input: CreateRecordInput` as a literal parameter name, which `ruff`'s enabled `A002` rule (flake8-builtins) refuses. Untested until this slice, since slice 1's resolvers happened to avoid these three names. `ruff`'s config excludes `*.md` and `rules/` from linting, so the doc's own example was never actually checked against the lint config it's meant to satisfy | None to the schema — the GraphQL field names are unchanged, only the Python-side parameter names differ from the doc's illustrative naming |
| D-27 | The `records` query returns `[Task!]!` directly, not a separate `RecordSummary` type the sub-plan's file table named | Drafted, then reverted during review: with one record type this epic, a `RecordSummary` projection would carry the same fields `Task` already has, plus a `recordType` field whose value never varies ("task"), for no behavioural gain and one more DTO-to-type mapping to maintain. The canvas's "Type" column is a static "Task" label the frontend can render directly, the same way the mockup itself hardcodes it | The `records` list and `record(id)` detail share one type end to end. A second record type in a later epic is what actually justifies `RecordSummary`, added then with a change record |
| D-28 | `identity/models.py`'s `UserSettings` gained `created_at` in addition to the `user_id`/`timezone` the sub-plan's file table named | Every other table in this schema carries `created_at`/`updated_at`; T-2.10's own test case ("a second call returns the same row, not a new one") needs `created_at` to prove identity, not just value equality | Additive column, no contract change |
| D-29 | Query operation hooks (`useGetRecords`, `useGetRecordDetail`, `useGetTasks`, `useGetSettings`) use `useLazyQuery` plus a `useEffect` in the controller that calls the operation's `responseHandler` itself, instead of an `onCompleted` callback | Apollo Client 4 removed `onCompleted`/`onError` from `useLazyQuery` entirely (verified against its type definitions) — this was already how repo-rules.md §6.2's own query example was shaped, since only its mutation example used `onCompleted`; not a deviation from the documented pattern, only from an assumption made mid-slice | None; mutations (`updateTask`, `completeTask`, `deleteTask`, `updateTimezone`) still use `onCompleted` via `useMutation`, which Apollo Client 4 keeps |
| D-30 | `completeTask` has no UI trigger in this slice; `RecordEditForm` sends a status change through `updateTask` alongside the title, one "Save changes" button, one call | `RecordEdit.dc.html` draws a single save action for both fields, no separate complete affordance. The `CompleteTask` operation folder and its response-handler test were still built, per the task list, and sit ready for a future quick-complete control (a checkbox in `RecordTable`, say) that the canvas does not currently draw | `completeTask` is reachable over GraphQL and tested, just not wired to a click anywhere yet |
| D-31 | `DeleteConfirmModal`'s only real caller is `RecordDetailController`, deleting one id | The canvas draws no multi-select UI in `RecordTable`, so bulk delete (FR-21) has no UI to call it from yet. The component's props already accept a count for that future case | `deleteTask`'s multi-id path is proven at the interactor level (`test_delete_tasks_interactor.py`) and reachable over GraphQL; no frontend UI calls it with more than one id yet |
| D-32 | A sidebar app shell (`src/app/AppShell.tsx`) was built this slice, wrapping all three routes (`/`, `/records`, `/settings`) with the rail nav every canvas artboard draws | Neither slice's file table itemised it. Slice 1 shipped `CommandCenterController` as the sole full-page component with no way to navigate anywhere else, which was fine with one destination; slice 2 adds two more real destinations that would otherwise be reachable only by typing a URL | `router.tsx` now nests all three page components under one layout route. Slice 3 (installed app and theme) inherits a real shell to attach to, rather than needing to build one itself |
| D-43 | Added 2026-09-14, well after this slice shipped: due-date editing, deferred at the time (D-30's sibling note, and `04.2`'s own FR-19 row). `UpdateTaskInput` gained `dueAt: datetime \| None = strawberry.UNSET`; `title`/`status` didn't need `UNSET` since neither is legitimately absent, but a due date legitimately clears to null, so "not provided" and "explicitly cleared" have to be distinguishable. `RecordEditForm` uses a `datetime-local` input rather than a date-only one, since `due_at` is a full instant, not a calendar date | User asked to complete the due-date control | Backend: `UpdateTaskInput.due_at`, `UpdateTaskInputDTO.due_at`/`due_at_provided`, `TaskRepository.update`'s two new params, 6 interactor tests (was 4). Frontend: `RecordEditForm`'s due field is now a live input, `RecordDetailController` tracks `draftDueAt`, `formatDate.ts` gained `toDateTimeLocalInputValue`/`fromDateTimeLocalInputValue`. A real bug surfaced live (see incidents, I-9) and was fixed the same pass |

### Incidents and defects

| # | What broke | Cause | Fix |
|---|---|---|---|
| I-9 | Added 2026-09-14, during D-43's live check: typing into the `datetime-local` input's day/month/year segments out of order (a real, easy-to-hit interaction, not a contrived one) threw an uncaught `RangeError: Invalid time value` from `fromDateTimeLocalInputValue`, visible in the browser console | The function assumed a non-empty input value is always a `Date`-parseable string. A `datetime-local` input reports `""` while a segment is genuinely incomplete, but can transiently report a value with an out-of-range component (a 5-digit year from typing digits into the wrong segment) that looks non-empty but that `new Date()` turns into an Invalid Date, and `.toISOString()` on that throws rather than returning a sentinel | Added an `Number.isNaN(date.getTime())` guard, treating an unparseable in-progress value the same as "no due date" rather than throwing. Caught by clicking through the real control in a live browser, not by the unit tests written alongside the fix — a `formatDate.test.ts` case now locks in the exact input string that crashed it |

## Slice 3 — Installed App and Theme

Frontend only, built and verified 2026-09-14. Two background attempts at this
slice were killed mid-work (see incidents); the work was finished directly.

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-3.1 | Three icon assets from the design canvas's PWAIdentity artboard | **done** | Generated programmatically (Pillow) from the artboard's own SVG path and colours, not hand-drawn or screenshotted |
| T-3.2 | `vite-plugin-pwa` installed and configured | **done** | `injectManifest` strategy, not the plan's implied default, so `src/sw.ts` can read a POST body — see deviations |
| T-3.3 | `useOnlineStatus`, wired into the Capture input | **done** | Lives in `src/hooks/`, not `src/pwa/` — see deviations |
| T-3.4 | `InstallPrompt`, once-per-session logic | **done** | Lives in `src/components/` — see deviations |
| T-3.5 | `OfflineBanner` | **done** | |
| T-3.6 | `useUpdateAvailable` and `UpdateBanner` | **done** | |
| T-3.7 | Dark-mode audit | **done** | Clean: no raw hex or arbitrary Tailwind colour values found outside `tokens.css` anywhere in `src/` |

### Verification

| Check | Result |
|---|---|
| `npx tsc -b --noEmit` / `npx oxlint` | Clean |
| `npm run test` (Vitest) | **25 passed**, including `InstallPrompt` (T-3.1, T-3.2) and `UpdateBanner` (T-3.5) tests added after the background attempts were interrupted |
| `npm run build` | Clean; emits `dist/manifest.webmanifest` and `dist/sw.js` (13 precached entries, 889 KiB) |
| Manual browser pass, real production build (`vite preview`), real backend, real Supabase session | Chrome's own installability check fired a real `beforeinstallprompt`, proving the manifest, icons and service worker all satisfy its criteria independently of this project's own claims. Records, a record's detail, Capture and Settings all checked with dark mode active: every surface renders from dark tokens |
| Offline read (FR-40, T-3.3) | With the backend process stopped entirely (not just `navigator.onLine` toggled — a stronger test, since it proves the service worker's network-failure path, not just a client-side flag), reloading `/records` still rendered all three real tasks from the service worker's cache. Cache key strategy: `src/sw.ts` reads each request's cloned JSON body for `operationName`, caches only `GetRecords`/`GetRecordDetail`/`GetTasks`/`GetSettings` under a synthetic key folding in the operation name and variables (`${url}?operation=...&variables=...`), and never caches a mutation |

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-33 | `vite-plugin-pwa` uses the `injectManifest` strategy with a hand-written `src/sw.ts`, not the default `generateSW` strategy the sub-plan's file table implies (`workbox.runtimeCaching` as declarative config) | `generateSW`'s runtime-caching config is serialised into the built worker rather than executed as real code, so it cannot inspect a POST body. Every GraphQL operation is a POST to one URL, distinguished only by the JSON body's `operationName` — `generateSW` cannot tell `records` apart from `submitCapture`, let alone cache only reads. `injectManifest` hands fetch handling to real, testable code | `frontend/tsconfig.json` gained a third project reference, `tsconfig.sw.json` (the service worker needs the `WebWorker` lib, which conflicts with the app project's `DOM` lib in one program). `src/sw.ts` is the one file in this codebase that is a service worker, not app code, and is excluded from the app's own type-check for that reason |
| D-34 | `src/hooks/useOnlineStatus.ts`, `src/hooks/useUpdateAvailable.ts` and `src/components/{InstallPrompt,OfflineBanner,UpdateBanner}.tsx` live under the general-purpose `src/hooks/`/`src/components/` frontend repo-rules.md §3 already names, not a bespoke `src/pwa/` folder the sub-plan's file table suggested | `src/pwa/` is not itself part of the standing directory tree in repo-rules.md; `hooks/` and `components/` (cross-feature, presentational) already are, and these five files fit those definitions exactly | None to behaviour. Any future PWA-specific file should follow the same placement rather than reviving `src/pwa/` |
| D-35 | `formatDueDate.ts` (capture) and `formatDate.ts` (records) were consolidated into one shared `src/utils/formatDate.ts` | Found duplicated during this slice's work: both features formatted the same `Task.dueAt` shape for display, one file per feature. Not itemised in any sub-plan, a small cleanup made while touching adjacent files | `TurnCard.tsx` and `RecordTable.tsx`/`RecordEditForm.tsx`/`RecordDetailController.tsx` all import from the one shared location now; the two feature-local files are deleted |
| D-36 | The offline note is the Capture input's own placeholder text ("You're offline") plus the ambient `OfflineBanner` in the app shell, not a third `note`/`refused`-style card inserted into the capture stream itself | FR-40 asks for an inline refusal before submit; changing the input's own appearance (dimmed, placeholder swapped, disabled) plus a persistent banner already state this clearly across every route without adding a card that would need its own dismiss/retry affordance for a state that resolves itself the moment the network returns | None; no capture turn is created for a blocked offline attempt, matching "nothing is queued" |

### Incidents and defects

| # | What broke | Cause | Fix |
|---|---|---|---|
| I-5 | A background agent building this slice was killed by the user while `vite.config.ts` referenced `src/sw.ts` before that file existed, 500-ing the user's own dev server mid-test | The agent saved an intermediate state where the PWA plugin pointed at a service worker file it had not yet created; Vite restarts on every `vite.config.ts` change, so the user's live tab hit the broken intermediate state | `src/sw.ts` was created moments later by the same agent and the dev server recovered on its own before this was investigated further. A second, briefed-with-this-constraint attempt at the same slice was also killed later, independently, by an account-level session rate limit rather than this failure mode recurring |
| I-6 | Two background attempts at this slice both terminated with `HTTP 429` ("You've hit your session limit"), the second mid-way through wiring the Capture input | Account-level rate limiting, unrelated to the task. Not a code defect | The slice was finished directly instead of through a third background attempt. Partial work from the second attempt (hooks, components, `sw.ts`, `vite.config.ts`, one test file with a stale mock path) was inspected file-by-file and completed rather than restarted, after independently re-verifying every piece against the sub-plan |
| I-7 | The first `InstallPrompt`/`UpdateBanner` test attempts using a raw DOM `.click()` and `window.dispatchEvent()` outside `act()` did not update component state before the assertion ran | Standard React Testing Library gap: a native event dispatched on `window` for a listener registered via `useEffect`'s own `addEventListener` is not wrapped in React's `act()` the way `render()` or `fireEvent` calls are | Rewrote the three affected dispatches to use `act()` (for `beforeinstallprompt`/`appinstalled`) and RTL's `fireEvent.click` (for button clicks) |

## Slice 4 — Chat History and Loading Feedback

Backend and frontend, built and verified 2026-09-14. FR-44 to FR-46.

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-4.1 | `0006_capture_turns` migration, RLS policy | **done** | Applied, downgraded and re-applied cleanly against the real database |
| T-4.2 | `CaptureTurnDTO`, `CaptureHistoryPageDTO`, `CaptureTurnRepository` Protocol, `SqlCaptureTurnRepository` | **done** | Also carries `resulting_pending_capture_id`, `question_text`, `answer_text` beyond the sub-plan's first draft — see deviations |
| T-4.3 | `submit_capture`, `answer_pending_capture`, `discard_pending_capture` each take and call `capture_turn_repository` | **done** | |
| T-4.4 | `ListCaptureHistoryInteractor`, `captureHistory` query, `deps.py` wiring, `CaptureQueries` added to the schema | **done** | |
| T-4.5 | `InlineSpinner` component | **done** | `src/components/`, alongside `InstallPrompt`/`OfflineBanner`/`UpdateBanner` |
| T-4.6 | `RecordEditForm`'s `isSaving` prop, `RecordDetailController` wiring | **done** | |
| T-4.7 | `TurnCard`'s `isAnswering` prop, `CommandCenterController`'s `submittingTurnId` wiring | **done** | |
| T-4.8 | `GetCaptureHistory` operation folder, `CaptureTurnFields` fragment, codegen run | **done** | |
| T-4.9 | `HistoryPanel`, history icon in the Capture topbar | **done** | |

### Verification

| Check | Result |
|---|---|
| `mypy --strict app` / `ruff check app tests` | Clean |
| `pytest tests/unit` | **75 passed** (was 70; +5 for this slice) |
| `pytest tests/integration -m "not live"` | **49 passed** (was 46; +3 for this slice) |
| `alembic upgrade head` / `downgrade -1` / `upgrade head` | Clean round-trip against the real database |
| `npx tsc -b --noEmit` / `npx oxlint` | Clean |
| `npm run test` (Vitest) | **35 passed** (was 25; +10: `RecordEditForm`, `TurnCard`, `HistoryPanel`) |
| `npm run build` | Clean |
| Manual browser pass, real backend (restarted to pick up the new schema — see incidents), real Supabase session | Ran `/add-task` with no arguments, answered the resulting question, opened History: both turns showed, most recent first, correctly correlated (the answered turn showed the question it resolved and the answer given) — this is the two-rows-per-thread reading that motivated D-41, found here and fixed the same day. Edited the created task's status to Done from Records; the edit form's Save round-tripped and the detail view showed the new status and last-edited time |
| Capture history drawn on the canvas (`CaptureHistory`, `CaptureHistoryStates`, `MobileCaptureHistory`); D-41's merge fix | `npx tsc -b --noEmit` / `npx oxlint` clean; `npm run test` **37 passed** (was 35; +2 for the merge fix). Both dev servers restarted and the fix clicked through live in a real browser session against the real backend and the real thread created earlier in this dev log: the answered thread rendered as one row, and a freshly-asked, still-unanswered question rendered as its own row, both correctly. This live pass is what caught D-42 below — the mock-data component tests alone had not |

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-37 | `capture_turns` gained `resulting_pending_capture_id`, `question_text` and `answer_text`, beyond the sub-plan's first-drafted `resulting_task_id`-only shape | Found while drafting, before any code was written, in answer to the user asking whether an asked question is recorded at all: `pending_captures` deletes its row on resolution (FR-37), so without capturing the question and answer text onto the turn itself, history would lose the wording for every resolved question, the exact case FR-44 exists to cover | Sub-plan `04.4` updated in place before approval; no rework. The `task_created` row written by `answer_pending_capture` carries both `resulting_task_id` and `resulting_pending_capture_id`, which is what lets a history view later correlate it back to the `question_asked` row for the same thread |
| D-38 | `discard_pending_capture` now raises `PendingCaptureNotFoundError` when the pending capture does not exist, where it previously did nothing silently | FR-44 needs the pending capture's `original_input` and `question_text` before it is deleted, which means fetching it first; once fetched, a missing row is indistinguishable from the case `answer_pending_capture` already treats as an error | No existing test asserted the old silent behaviour. Matches `answer_pending_capture`'s existing treatment of the same not-found case: a plain GraphQL error, not a union member, since the frontend never holds an id it did not receive from its own account |
| D-39 | The Capture page's pending-question answer control has no dedicated submit button; `InlineSpinner` renders inside the answer field itself during `isAnswering`, not on a button | Slice 1 shipped this control as Enter-to-submit only, with no button. Adding one to show a spinner on would have been new UI beyond this slice's scope (loading feedback on an existing control, not a new control) | `Discard` is disabled during `isAnswering`; the input is disabled and the spinner appears beside it |
| D-40 | Answering two different pending questions in close succession can clear the first one's spinner early, since `CommandCenterController`'s `submittingTurnId` tracks only the most recently submitted answer | `useAnswerPendingCapture` is one mutation tuple per component instance; Apollo's `loading` reflects the most recent call, not a per-call flag. Fixing this properly needs per-call tracking, which is more than loading feedback needs | Accepted as a known edge case in the sub-plan before it shipped, not discovered afterward. Named here per rule 5 regardless |
| D-41 | `HistoryPanel.tsx` now shows one row per thread, not one per `capture_turns` write: a `question_asked` row is filtered from the rendered list once a later loaded row's `resultingPendingCaptureId` correlates to it | Found during this slice's own manual QA (the verification row above): a resolved question showed as two near-duplicate rows, the original question and a second row repeating it alongside the answer. `capture_turns` is insert-only by design (build plan §3), so both rows still exist in the query result; this is a display-only filter, computed client-side over the currently loaded page(s) | Two component tests added (`HistoryPanel.test.tsx`): a resolved thread renders once, a still-open question keeps its own row. Documented in `02-design.md`'s Capture history section, including the accepted edge case of a thread split across a "Load more" page boundary |
| D-42 | D-41's first correlation check was wrong: it compared a `question_asked` row's own `id` against other rows' `resultingPendingCaptureId`. The correct check compares each row's `resultingPendingCaptureId` against every other row's — a `question_asked` turn's `id` is the id of its own `capture_turns` write, never the pending capture's id; `resultingPendingCaptureId` is where that pending capture's id actually lives, on both the asking row and the resolving row | Caught live, not by the two D-41 tests: a real browser session against the real thread created earlier in this dev log still showed two rows after D-41 shipped. The mocked test data had used the same wrong shape the bug matched (a question row's `id` set to the value the fix looked for), so both tests passed against incorrect logic | Read the real `captureHistory` response via a direct `fetch` in the browser console to see the actual field values before touching code again. Fixed the filter, corrected both D-41 tests to the real field shape, re-verified live: an already-answered thread showed one row, a freshly-asked unanswered question showed its own row |

### Not done, and why

RecordEditForm's due date field renders read-only; there is no control to change it, and `completeTask` exists as a mutation with no UI calling it — completion happens by setting status to Done in the same form. Found while drafting this slice, not fixed: FR-19's "any field the user supplied" is not fully built for due date, but building that control is new functionality, not loading feedback on an existing one. Named in `04.4` section 4 before any code was written, same treatment as slice 3's reload-loses-input gap.

### Incidents and defects

| # | What broke | Cause | Fix |
|---|---|---|---|
| I-8 | The manual browser pass initially failed with `Cannot query field 'captureHistory' on type 'Query'` even though the code was correct and unit/integration tests passed | The running backend process (`uvicorn`, started earlier in the session for manual testing) had no `--reload` flag, so it never picked up any of this slice's code changes, including ones made hours earlier | Restarted the process. Not a code defect; worth remembering that this repo's dev server is not auto-reloading unless started with `--reload` |

## Changed by later epics

| # | Change | Why | Consequence |
|---|---|---|---|
| D-44 | Added 2026-09-23 by epic 003, task T-1.13 of its sub-plan 4.1. Every extraction now carries the user's own date and zone: `GatewayExtractionAdapter` takes a `LocalClockPort` and appends "Now is {local ISO time} ({IANA zone})." to the instruction. `/add-task Finish docs tomorrow` for a user in Asia/Kolkata now means tomorrow in Kolkata, not tomorrow in UTC | 003's build plan AD-7: reminders need the user's local now to read "tomorrow at 7", and reading tasks against a different clock than reminders would let the two disagree about the same word | Task capture's due dates change for any user whose zone is far from UTC around midnight, which is the fix. Covered by 003's TC-1.16, `test_every_extraction_reads_dates_against_the_users_local_now`. 003's dev log D-8 is the other half |
| D-45 | Added 2026-09-26, found while live-testing epic 003's reminders on the shared Records page. `RecordsController.tsx` computed `hasLoadedOnce = apiStatus === API_SUCCESS`, which stayed true across a tab/search/sort change until the new request's response landed, since `apiStatus` never reset and the refetch is itself debounced 250ms. Switching from All to Tasks briefly rendered a bare "0 records" instead of the loading skeleton. Fixed with a `committedFilterKey` compared against the current filter key, reset during render (React's documented pattern), so `isFilterPending` goes true the instant the filter changes and only clears once a response for that exact filter lands | The user saw the flash live and asked for the skeleton to show immediately on every tab switch, with a real empty view per tab rather than a bare table | The Tasks tab also gained its own true-empty ("No tasks yet") and no-match ("No tasks match "...") views via the existing `ReminderListNotice`, matching `EmptyReminders`/`RemindersController`'s established pattern; the All tab's original full-page `EmptyRecords` is unchanged for a first-ever empty account, and gained the same no-match treatment. Three new tests in `RecordsController.test.tsx`; `tsc -b`, `oxlint`, `vitest run` (153 passed) all clean |

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-13 | Slice 1 backend built and verified: 2 domains, 2 migrations, 9 backend files beyond the original file-by-file plan (D-17's `list_open_tasks` addition), 83 tests passing including one real Gemini call. Frontend not started | User asked to build slice 1 | user |
| 2026-09-13 | Slice 1 frontend built and verified: project bootstrapped from scratch (Vite, Tailwind v4, Apollo Client 4, MobX, codegen), `tokens.css`, three operation folders, `CaptureStore`, `CommandCenterController` and its components, ported from the canvas's `Main.dc.html`. Verified against the real backend, real database and real Gemini in a browser, all five capture flows (add-task with a date, add-task without one, `/tasks`, non-command, unrecognised command) | User asked to bootstrap the frontend and finish slice 1's UI | user |
| 2026-09-13 | Slice 2 backend built and verified: `records` extended (5 new repository methods, 4 interactors, a full `graphql/` folder), `identity` domain built from scratch, 1 migration, 116 tests passing (70 unit, 46 integration) | User asked to build slice 2 | user |
| 2026-09-13 | Slice 2 frontend built and verified: 8 operation folders, `RecordsStore`/`SettingsStore`, `RecordsController`/`RecordDetailController`/`SettingsController` and their components, a new sidebar app shell (D-32), Vitest and React Testing Library installed for the first time. Verified against the real backend and a real Supabase session in a browser: list, detail, edit, complete-via-edit, delete, search, and timezone change all confirmed working | User asked to build slice 2 | user |
| 2026-09-14 | Slice 3 built and verified: `vite-plugin-pwa` with a hand-written service worker for GraphQL-aware offline caching (D-33), install/offline/update UI, a clean dark-mode audit across every screen from slices 1-2. Verified against a real production build: Chrome's own installability check, and a real offline read proven by stopping the backend outright, not just toggling a client-side flag. Feature 001 (all three slices) is now feature-complete pending the open sign-in-screen gap noted after slice 1 | User asked to build slice 3 | user |
| 2026-09-14 | Slice 4 built and verified: `capture_turns` table and `captureHistory` query (with `question_text`/`answer_text` added mid-draft, D-37), a history panel on the Capture page, and loading feedback on the task edit form's Save action and on answering a pending question. 124 backend tests passing (75 unit, 49 integration), 35 frontend tests passing. Found and logged, not fixed: `RecordEditForm` has no due-date control | User approved `04.4` and asked to build it | user |
| 2026-09-14 | Capture history designed on the canvas (`CaptureHistory`, `CaptureHistoryStates`, `MobileCaptureHistory`) and a one-row-per-thread merge rule found during manual QA (D-41), decided in `02-design.md` and implemented in `HistoryPanel.tsx`. 37 frontend tests passing | User asked for good UX/UI on capture history added to the designs, then to implement the merge fix | user |
| 2026-09-14 | D-41's merge logic corrected (D-42): the first version compared the wrong pair of fields and passed its own tests against test data that shared the bug. Caught live, both dev servers restarted for the check, re-verified against a real answered thread and a freshly created unanswered one | User asked to start the servers and click through it | user |
| 2026-09-14 | The due-date gap logged after slice 4 closed (D-43): `updateTask` now accepts `dueAt`, `RecordEditForm`'s due field is a live `datetime-local` input, both setting and clearing a due date work end to end. A crash found live in the same pass (I-9) was fixed before this was called done | User asked to complete the record edit form's due-date control | user |
| 2026-09-14 | `04-implementation-plan.md` §8's five cross-slice cases checked against reality: T-X.1 and T-X.2 live in a browser (a task created via Capture showed up in Records on normal navigation, no hard reload; an edited title survived a navigate-away-and-back with origin still "Command"), T-X.3 cross-referenced to four existing per-table boundary tests plus the RLS sweep, T-X.4/T-X.5 cross-referenced to slice 3's own dev log entries. §11's Definition of Done audited line by line: migrations and cross-slice cases now checked off; PRD §8's seven metrics checked honestly rather than assumed — 3 already covered by data that already exists (`tasks`, epic 000's `ai_usage`), 1 partial (edits yes via `updated_at`, deletes no since `deleteTask` hard-deletes with no audit trail), 3 genuinely not covered (FR-9 sessions and records-view opens have no event source at all; cohort retention is blocked on epic 002's accounts, which don't exist yet). `index.md` left at `in-review`, not `shipped`, since the metrics gap is real, not a checklist formality | User asked to record the two open Definition-of-Done items and commit | user |
| 2026-09-19 | Two of the three real PRD §8 metric gaps closed (see `04-implementation-plan.md`'s own change log entry for the full description). **Deviation, per root `CLAUDE.md` rule 2:** this is new scope on an approved, locked implementation plan (`04-implementation-plan.md`, `approved_on: 2026-09-13`), added directly rather than through a full change-control re-review, on the user's explicit instruction to proceed after the missing approval was named. Soft delete was the user's own call, not Claude's: "use soft delete dont hard delete any data record." Backend: new `analytics` domain (`app/domains/analytics/`, one table `events`, migration `0014_events`), `tasks` gains `deleted_at` (migration `0013_tasks_soft_delete`), `TaskRepository.delete_many` changed from a hard `DELETE` to an `UPDATE ... SET deleted_at`, every task read path filters `deleted_at IS NULL`. `submit_capture.py` takes a new `AnalyticsPort` collaborator and logs `no_command_input` on the guidance branch; records gets a new `recordsViewOpened` mutation logging `records_view_opened`, wired into `RecordsController`'s mount effect. `backend`: 91 unit tests passing (was 89, +2 new files), `mypy --strict` clean (3 pre-existing unrelated errors in untouched files), `ruff` clean, `test_layering.py` and the alembic migration chain both clean. Two integration test files updated (`test_records_graphql.py`, `test_capture_graphql.py`) and one new integration assertion added for the `recordsViewOpened` mutation — **not run against a live database**, no Postgres reachable from this environment, same constraint noted for slice 3's integration suite; type-checked and lint-checked only. Migrations not applied to any database for the same reason. `frontend`: `frontend/schema.graphql` regenerated from the live backend schema via `strawberry.printer.print_schema` (the committed command from T-1.11), a new `RecordsViewOpened` mutation operation folder added via `npm run codegen`, `RecordsController` fires it once on mount. `npm run test` (58 passed), `npm run lint`, `npm run build` all clean. Not manually verified in a running browser | User: "use soft delete dont hard delete any data record, proceed with the implementation" | user |
| 2026-09-23 | D-44 recorded: extraction reads dates against the user's local now, a change made by epic 003's AD-7 | Epic 003 sub-plan 4.1, T-1.13 | user |
