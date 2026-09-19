---
doc: dev-log
feature: 000-ai-gateway
title: AI Gateway and Usage
stage: 5
status: draft
owner: user
created: 2026-09-12
updated: 2026-09-19
approved_on: null
supersedes: null
---

# Dev Log — AI Gateway and Usage

Context: [Index](./04-implementation-plan.md) · [04.1](./04.1-api-skeleton.md)

What actually happened. Deviations from the approved plan are recorded the day
they happen, per rule 5 of the root ruleset.

## Slice 1 — API Skeleton

Started and largely completed 2026-09-12.

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-1.1 | Layout, virtual environment, install, pin versions | **done** | Versions below |
| T-1.2 | `core/settings.py`, `.env.example`, `.gitignore` | **done** | |
| T-1.3 | `core/logging.py` with redaction | **done** | |
| T-1.4 | `app/main.py`, `/health`, middleware, exception handler | **done** | |
| T-1.5 | `graphql/schema.py`, mounted | **done** | |
| T-1.6 | `Dockerfile`, confirm the image starts | **partial** | Written. **Not verified**, see deviation D-1 |
| T-1.7 | CI: ruff, mypy, pytest, secret scan | **partial** | Written. **Not verified**, see deviation D-2 |

### Resolved dependency versions

Pinned from PyPI on 2026-09-12, per T-1.1. Rule 7 of the process: these are read
from the install, not from memory.

| Package | Version | | Package | Version |
|---|---|---|---|---|
| fastapi | 0.141.1 | | pytest | 9.1.1 |
| uvicorn | 0.52.4 | | pytest-asyncio | 1.4.0 |
| strawberry-graphql | 0.327.7 | | httpx | 0.28.1 |
| pydantic-settings | 2.15.0 | | ruff | 0.16.7 |
| structlog | 26.1.0 | | mypy | 2.3.1 |

43 packages resolved in total, including transitive. Python 3.12.10.

### Verification

| Check | Result |
|---|---|
| `pytest` | **13 passed** |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 15 files already formatted |
| `mypy app` (strict) | No issues in 7 source files |
| `uvicorn` then `GET /health` | `200 {"status":"ok"}` |
| `uvicorn` then `POST /graphql` | `200 {"data":{"apiVersion":"0.1.0"}}` |

Section 1 of 04.1 is demonstrably true: the server starts and answers both
endpoints over real HTTP.

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-1 | T-1.6's acceptance check, `docker run` then curl, was **not performed** | Docker is not installed on this machine, or its daemon is not running | The `Dockerfile` is unverified. It is plausible and conventional, and it has never been built. Must be run before slice 1 is called done. **Still open**, see 2026-09-13 below |
| D-2 | T-1.7's acceptance checks were **not performed**: CI has never run, and the secret scan has never been proven to fail on a planted key | The workflow cannot run until the branch is pushed, and nothing has been pushed | The second check is the one that matters. A secret scan that has never failed has never been tested. **Resolved 2026-09-13**, see below |
| D-3 | 20 files created, against 17 planned | Package markers `tests/integration/__init__.py` and `app/__init__.py` were not itemised in the plan, and the settings and redaction tests were split into two files at `tests/` root rather than sitting under `tests/integration/` | None. They are unit tests and do not belong under `integration/` |
| D-4 | `.github/workflows/ci.yml` sits at the repository root, not under `backend/` | CI covers the whole repository, and the frontend will add a job to the same file | None. The plan's path was written as if the backend owned it |

### 2026-09-13 — CI proven, D-2 closed and a new gap found

The branch was pushed for the first time today, to a now-public repo. Findings:

**The `secrets` job works, once the planted secret is a real match.** A first
attempt planted a Google-style key using a sequential-alphabet placeholder
(`AIzaSy...ABCDEFGHIJKLMNOPQRSTUVWXYZ123456`); gitleaks scanned the exact diff
and reported no leaks, which was inconclusive rather than a working negative —
that value likely fails gitleaks' own heuristics, not a broken scanner. A
second attempt planting a PEM `-----BEGIN PRIVATE KEY-----` marker, which
gitleaks matches on the header alone, was caught: the job failed with "Leaks
detected". **D-2 is closed:** the scan has now been proven to fail on a real
match. Test performed on a throwaway branch (`throwaway/secret-scan-test`,
commits `b46d434` then `b6b07d6`), deleted afterward, local and remote.

**D-11 (new, closed same day): the `Tests` step failed in CI on every push,
including the real docs branch.** `Settings()` requires `gemini_api_key`,
`database_url`, `supabase_url` and `supabase_jwks_url`; the workflow set none of
them, so every test run died in `conftest.py` before a single test collected.
Lint, format and types all passed; only `Tests` failed. This was never caught
before today because nothing had been pushed since T-1.7 was written.

Fixed in `.github/workflows/ci.yml`: the `Tests` step now passes placeholder
values for the four settings as step-level `env`, and runs only
`tests/unit tests/test_settings.py tests/test_logging_redaction.py`, not the
whole `tests/` tree. Verified locally with `.env` moved aside so no real value
could mask the check: 43 tests pass on the placeholder env alone.

**`tests/integration/` is deliberately excluded from CI, not fixed.** It needs
a real Supabase-shaped Postgres database, including an `auth.users` table and
the RLS policies, which CI does not provision. Standing up that database is a
real decision (a service container mimicking Supabase's schema, or a scoped
test project) and is left open rather than answered by a placeholder database
that would silently pass without a database at all. Until it is answered, the
`Tests` step covers unit tests only, and RLS, permissions, and the union
mapping are proven locally, not in CI.

**D-1 deferred, not resolved.** Docker still is not installed on this machine.
User direction 2026-09-13: Docker and production concerns are deferred until
after the product is built; development proceeds without that verification for
now. D-1 is not a slice 1 definition-of-done item (04.1 section 9 requires CI
green and the secret-scan proof, not the image build), so this does not block
slice 1. It must be revisited before shipping.

### Not done, and why

Slice 1's own definition of done (04.1 section 9) is now met: CI is green on
commit `627ec3b` (both jobs, [run 34741143619](https://github.com/SSC369/jarvis/actions/runs/34741143619)),
and the secret scan is proven to fail on a real planted key. D-1 (the Docker
image) is deferred by user direction, not a DoD item for this slice, so slice 1
is otherwise complete.

What remains, tracked against the feature-level DoD in `04-implementation-plan.md`
section 11, not this slice:

1. Build the image and confirm it answers `/health` — deferred until after the
   product is built, per user direction 2026-09-13.
2. Stand up a real database for `tests/integration/` in CI, so RLS, permissions
   and the union mapping are proven there too, not only locally.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-12 | Created. Slice 1 tasks T-1.1 to T-1.5 done, T-1.6 and T-1.7 partial | Slice 1 development began | — |
| 2026-09-13 | D-2 closed: secret scan proven against a real planted key. D-11 opened and closed same day: CI's `Tests` step, which failed on every push for lack of required settings, now runs unit tests only with placeholder env; CI is fully green for the first time (`627ec3b`). D-1 deferred by user direction, until after the product is built | First push to CI since the branch opened | user (D-1 deferral) |

## Slice 2 — Identity and Isolation

Built 2026-09-12.

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-2.1 | Packages added and pinned | **done** | Versions below |
| T-2.2 | Settings additions, `.env.example`, password redaction | **done** | |
| T-2.3 | `core/db.py`, engine, `user_transaction` | **done** | |
| T-2.4 | `core/auth.py`, JWKS verification | **done** | |
| T-2.5 | `context.py`, `errors.py`, `deps.py` | **done** | Contract change, see below |
| T-2.6 | Alembic and `0001_ai_usage` | **done** | |
| T-2.7 | `0002_ai_user_limit` | **done** | |
| T-2.8 | `IsAuthenticated`, `@map_errors`, context wired | **done** | |
| T-2.9 | Boundary tests | **done** | Including the negative proof |
| T-2.10 | Readiness check | **done** | `/ready`, separate from `/health` |

### Resolved dependency versions

| Package | Version |
|---|---|
| sqlalchemy | 2.0.52 |
| asyncpg | 0.31.0 |
| alembic | 1.20.0 |
| pyjwt | 2.14.0 |
| cryptography | 50.0.1 |

### Verification

| Check | Result |
|---|---|
| `pytest` | **33 passed** |
| `ruff check .` | All checks passed |
| `mypy app` (strict) | No issues in 18 source files |
| `alembic upgrade head` | Both migrations applied |
| `alembic downgrade base` | Both reversed, no enum left behind |
| `GET /health` | `200 {"status":"ok"}` |
| `GET /ready` | `200 {"status":"ok","database":"ok"}` against the live database |
| `{ apiVersion }` without a token | `200`, resolves |
| `{ me }` without a token | Refused, `Not authenticated` |
| Both tables | RLS enabled, forced, one policy, granted to `authenticated` |

**T-2.7 was seen to fail.** With `SET LOCAL ROLE` removed, it reported "no-identity
transaction saw 2 rows. Row Level Security is not binding". The definition of
done required this, and it is the only reason the test is worth having.

### Defects found and fixed during the slice

| # | Defect | How it surfaced | Fix |
|---|---|---|---|
| B-1 | `sa.Enum` re-issues `CREATE TYPE` inside `create_table`, colliding with the explicit statement | Migration failed on first apply | Use `postgresql.ENUM` with `create_type=False`, which is the only form that honours it |
| B-2 | Alembic passes the URL through `configparser`, which treats `%` as interpolation. A percent-encoded password raises, **and the raise renders the whole DSN including the password** | `alembic current` failed | `env.py` passes the URL straight to the engine, bypassing `configparser`. Comment left at the line |
| B-3 | The lifespan never opened the connection pool | `/ready` returned 503 and `{ me }` returned 500 against a running server | The edit that added it had silently no-op'd. Restored, and `test_lifespan_populates_application_state` now guards it |

**B-3 is the one worth remembering.** Every test passed while the server could
not serve a single GraphQL request, because the client fixture sets `app.state`
by hand and papered over the missing lifespan. A fixture that supplies what the
application should build itself will hide the application failing to build it.

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-5 | `Context` is not frozen, against the index's contract | Strawberry accepts only `BaseContext` or a dictionary, and writes `request` and `response` onto it at runtime | Change record filed in the index section 4. FR-6 is unaffected |
| D-6 | 22 paths touched, against 21 planned | `app/models/__init__.py` needed a package directory, and `tests/integration/test_graphql_auth.py` was added | None |
| D-7 | Strawberry logs a full traceback at error level when a permission class refuses | Its own behaviour, not ours | Noisy logs on every unauthenticated call. Worth suppressing before production. Not a security issue: the client still receives only "Not authenticated" |

### Security note

The database password was printed in full in a terminal traceback during B-2,
before the fix. **It must be rotated**, and the `.env` value replaced with the
percent-encoded form of the new password.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-12 | Slice 2 recorded. All ten tasks done, three defects found and fixed, three deviations | Slice 2 development completed | — |

## Slice 3 — The Gateway

Built and committed 2026-09-13, commit `4a3d2c0`.

### Tasks

| # | Task | Status | Note |
|---|---|---|---|
| T-3.1 | Packages pinned, settings extended, key in `secret_values()` | **done** | Versions below |
| T-3.2 | `models.py`, `interfaces/`, `constants.py` | **done** | |
| T-3.3 | `errors.py`, six members and exceptions | **done** | |
| T-3.4 | `usage_repository.py` | **done** | |
| T-3.5 | `allowance_service.py` | **done** | |
| T-3.6 | `langchain_provider.py`, timeout, retry, exception unwrapping | **done** | |
| T-3.7 | `extraction_service.py` | **done** | Shipped as `ExtractInteractor` in `interactors/`, per the change already logged against 04.3 on 2026-09-12 |
| T-3.8 | `public.py` and `deps.py` wiring | **done** | |
| T-3.9 | Fakes and the unit suite | **done** | |
| T-3.10 | The live test, one real call | **done** | T-3.13 passed against `gemini-3.6-flash` |

### Resolved dependency versions

Pinned from PyPI on 2026-09-13, per rule 7.

| Package | Version |
|---|---|
| langchain-core | 1.6.3 |
| langchain-google-genai | 4.4.0 |

`langchain` itself was not added, per 04.3 section 4.

### Verification

| Check | Result |
|---|---|
| `pytest` | **69 passed**, including the live test against the real provider |
| `ruff check .` | All checks passed |
| `mypy app` (strict) | No issues in 35 source files |
| Live call to `gemini-3.6-flash` | Returned an `Extraction`, wrote one `ai_usage` row |
| `tests/unit/test_layering.py` | Enforces domain boundaries, vendor imports, acyclicity and adapter purity |

The fourteen cases in 04.3 section 8 pass. Section 1 of 04.3 is demonstrably
true.

### Deviations

| # | Deviation | Why | Consequence |
|---|---|---|---|
| D-8 | The Gemini client sits in `services/langchain_provider.py` and the use case in `interactors/extract.py` as `ExtractInteractor`, not `services/extraction_service.py` as 04.3 section 4 planned | User caught the client in the wrong folder during the slice; `adapters/` was removed as the gateway consumes no other domain | Already recorded as a 04.3 change on 2026-09-12. `public.py` exports `ExtractInteractor`, not `ExtractionService` |
| D-9 | The commit landed with several gateway methods taking positional arguments (`allowance_for(user_id, now)`, `usage_repository.record(usage, occurred_at)`, and others), against the keyword-only-calls rule adopted in commit `22c8c0e`, which predates this commit | The rule was adopted after 04.3 was drafted and the slice was not re-checked against it before committing | Fixed in commit `b7efa04`: every gateway call site and definition made keyword-only, `limit_for` renamed to `get_request_limit_for_user`, `build_extraction_service` renamed to `build_extract_interactor` to match `ExtractInteractor` |
| D-10 | `pyproject.toml` gained ruff's `ANN` rule set (with `ANN401` ignored at framework boundaries) and a `[tool.pyright]` section; `pyrightconfig.json` and `.vscode/settings.json` added | Needed to catch D-9 mechanically and to support editor type-checking | None functional. Committed alongside D-9's fix in `b7efa04` |

### Not done, and why

Slice 3's own definition of done (04.3 section 10) is not fully met:

1. **Provider-side spend cap: settled 2026-09-13, by decision rather than a
   console-configured billing budget.** User direction: the cap is the
   existing per-user limit, 20 commands per day (`DEFAULT_REQUESTS_PER_DAY` in
   `app/domains/gateway/constants.py`, already built and tested in slice 3),
   together with Tier 1's automatic 250 USD billing cap (build plan §11.3),
   rather than a separate dollar-denominated budget alert in the console. No
   further action on this item.
2. Langfuse (04.3 §6.3, Q3: wire without content capture) is not implemented.

D-1 and D-2 from slice 1 are resolved or deferred as of 2026-09-13, see slice
1's own section above.

The feature-level definition of done in `04-implementation-plan.md` section 11
is therefore not met, and `index.md` should not be moved to `shipped`.

### D-12 (new) — the account is back on free-tier rate limits

Checked 2026-09-13, prompted by confirming the spend cap. `03-build-plan.md`
recorded, on 2026-09-10 after billing was linked, paid-tier limits of RPM
10,000 / RPD 1,000 / TPM 1,000,000 for `gemini-3.6-flash` (build plan §5, Q7).
That number is what the whole capacity design rests on: a 20-call-per-user
daily default, a 1,000-request shared project ceiling, and a 50-user cap before
the ceiling is hit (build plan §5, §11).

The console now shows RPM 5 / RPD 20 / TPM 250,000, the free-tier numbers the
same section recorded *before* billing was linked. Confirmed operational, not a
design change: **billing has come unlinked from the project.**

At RPD 20 project-wide, `DEFAULT_REQUESTS_PER_DAY = 20` in
`app/domains/gateway/constants.py` alone consumes the entire project's daily
quota for one user. The gateway is not safely usable by more than one person
until billing is re-linked and the paid-tier limits are confirmed again in the
console.

**This blocks item 1 above**, since a spend cap is meaningless to set correctly
while the account is on the wrong tier. Re-link billing first, re-confirm RPM
10,000 / RPD 1,000 / TPM 1,000,000 (or whatever the console shows once fixed),
then set the spend cap and billing alert against the real paid-tier numbers.
The build plan's design itself is not reopened: this is an infrastructure
fault, not new information about what the design should have assumed.

**User direction 2026-09-13: proceed on the current free-tier limits (RPM 5,
RPD 20, TPM 250K) for now, rather than fixing billing first.** Consistent with
deferring Docker and production concerns until after the product is built.
Consequence, stated plainly: `DEFAULT_REQUESTS_PER_DAY = 20` per user now equals
the entire project's daily quota, so the gateway only behaves as designed for a
single active user (the developer, during this build). It is not safe to add a
second real user of the gateway until billing is re-linked and the paid-tier
numbers are confirmed again. The spend cap and billing alert (item 1 above)
stay deferred alongside D-1, for the same reason: there is no billing account
to cap while unlinked.

**D-12 closed, 2026-09-13.** Billing is re-linked; the console now reads RPM
1,000 / RPD 10,000 / TPM 2,000,000 for `gemini-3.6-flash`. `03-build-plan.md`
is updated to match, and the correction turned up something else: the
2026-09-10 reading had RPM and RPD transposed, so the real shared ceiling was
always meant to be 10,000, ten times the 1,000 the build plan's capacity
tables were built against. Every number moves in the safe direction. The
gateway is fine for more than one user again; `DEFAULT_REQUESTS_PER_DAY = 20`
is now a small fraction of the project ceiling, as originally intended.

The spend cap and billing alert (item 1) are still open, now unblocked. Tier 1
already caps total spend at 250 USD (build plan §11.3), which is a ceiling, not
an alert — nobody is told before it's hit. A billing budget alert at a much
lower threshold, closer to expected spend, is the piece still missing.

**Item 1 closed, 2026-09-19.** User set a Google Cloud budget alert at ₹100,
well under Tier 1's 250 USD cap. The provider-side spend cap and billing alert
line of section 11's definition of done is now met.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-13 | Slice 3 recorded. All ten tasks done, keyword-call/naming compliance fixed in `b7efa04`, spend cap and slice 1's CI/Docker gaps still unverified | Slice 3 development completed | — |
| 2026-09-13 | D-12 opened: billing has come unlinked from the Gemini project, account back on free-tier limits (RPD 20 vs. the paid RPD 1,000 the build plan assumed). Blocks the spend cap confirmation | Found while confirming the spend cap and billing alert | user |
| 2026-09-13 | D-12 closed: billing re-linked, real limits confirmed as RPM 1,000 / RPD 10,000 / TPM 2,000,000. The 2026-09-10 reading had RPM and RPD transposed. `03-build-plan.md` corrected: capacity tables rescaled 10x, a stray per-user cap of 50 fixed to 20, a stale `gemini-2.5-flash` reference fixed to `gemini-3.6-flash` | User reported updated rate limits | user |
| 2026-09-19 | Billing budget alert set at ₹100 in the Google Cloud console. Section 11's spend-cap-and-alert item closed | User set the alert | user |

### The index's five cross-slice cases (section 8)

Checked 2026-09-13 against `04-implementation-plan.md`'s own definition of
done, item 2.

| id | Status |
|---|---|
| T-X.1 | **Cannot be built yet.** It requires "a gateway-backed field", and the gateway domain has no `graphql/` folder and exposes no field by design — nothing calls it until epic 001 builds a domain that does (04-implementation-plan.md §9). Not a gap in this feature; a dependency on the next one |
| T-X.2 | Already covered by T-3.14 in `tests/integration/test_gateway_live.py` |
| T-X.3, T-X.4, T-X.5 | Buildable now without a GraphQL field, but a dedicated integration test would mostly restate what T-3.5 (per-outcome usage row), T-3.12 (key never logged) and the slice 2 RLS boundary tests already prove. Not written, for that reason, rather than left as an oversight |

The feature-level definition of done cannot be fully met until epic 001 exists.
This is expected, not a defect to chase now.

## Change log addendum

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-13 | Spend cap item settled: the existing 20-per-user-per-day limit plus Tier 1's automatic 250 USD cap serve as the provider-side spend control, by decision, rather than a separate Google Cloud billing budget alert | User decision | user |
