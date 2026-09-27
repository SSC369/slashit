---
doc: implementation-plan
feature: 002-authentication
title: Authentication
stage: 4
status: approved
owner: user
created: 2026-09-14
updated: 2026-09-27
approved_on: 2026-09-14
supersedes: null
split: true
---

# Implementation Plan (LLD) — Authentication

> **Approved** by @user on 2026-09-14. Locked — changes require a change record (§7).

Context: [PRD](./01-prd.md) · [Design](./02-design.md) · [Build plan](./03-build-plan.md)

No code is written before a sub-plan is itself approved.

## Tables touched

| Table | Change |
|---|---|
| `profiles` | new, slice 1 |
| `auth_attempts` | new, slice 1 |

## 1. Scope recap

Real signup, email verification, sign-in, password reset and Google sign-in,
replacing 001's dev-only console workaround. Manual signup and sign-in ship
first since every other slice, and every epic after 002, depends on a real
account existing at all. Google sign-in and password reset follow.

## 2. Split decision

| Trigger | Threshold | This feature |
|---|---|---|
| Tasks in the breakdown | more than 15 | Slice 1 alone is 13; three slices together exceed it |
| Files created or modified | more than 25 | Slice 1 alone touches about 20; three slices together exceed it |
| Independently shippable slices | more than one | Three: manual auth, password reset, Google |
| Distinct boundaries touched | more than two | Postgres/migrations, Auth Hooks, the identity backend domain, frontend routing and screens |
| Length of the drafted plan | more than 500 lines | Not reached, but the other four triggers are, on their own |

**Decision:** split into 3 sub-plans.

### Slices

| # | Sub-plan | What works when it lands | Depends on | Status |
|---|---|---|---|---|
| 1 | [04.1-manual-signup-and-signin.md](./04.1-manual-signup-and-signin.md) | A person creates an account, verifies it, signs in, sees their username, and 001's console workaround is gone | — | approved |
| 2 | [04.2-password-reset.md](./04.2-password-reset.md) | A person who forgot their password gets back in | 1 | draft |
| 3 | [04.3-google-sign-in.md](./04.3-google-sign-in.md) | A person signs up or in with Google instead | 1 | draft |
| 4 | [04.4-session-expiry.md](./04.4-session-expiry.md) | An expired or rejected session signs the user out with a notice, and nothing of it stays in the app | 1 | approved |

Slice 1 is approved; dev on it may start. 2 and 3 are drafted below it, per
§4's process rule allowing a later sub-plan to be written while an earlier one
is already in dev.

## 3. File-by-file plan

Split mode. Lives in each sub-plan.

## 4. Interfaces and contracts

Crossing slice boundaries, shared by all three.

**`profiles` (Postgres, created by slice 1).** `id` (PK, FK `auth.users.id`),
`username` (unique, case-insensitive, **nullable**), `created_at`. Nullable
because slice 3 (Google) creates a `profiles` row with no username: a person
who signs up through Google never types one. What a Google-created account's
username shows until the person sets one is slice 3's decision, not
re-litigated here; slice 1 only guarantees the column accepts null so slice 3
needs no migration of its own.

**`RequireAuth` (frontend, `frontend/src/app/RequireAuth.tsx`, created by
slice 1).** Wraps `AppShell`'s route in `router.tsx`. No session:
redirect to `/sign-in`. All three slices' routes that need a session (every
screen except the five auth screens themselves) sit inside it; no sub-plan
after 1 adds its own guard.

```ts
// GraphQL: app/domains/identity/graphql/queries.py, IdentityQueries.me
type Me {
  id: ID!
  email: String!
  username: String | null
}
```

`username: null` is a real, expected state (a Google-only account before
slice 3 gives it a way to set one), not an error. Every screen reading `me`
handles it.

## 5. Data and migrations

| Migration | Change | Reversible | Backfill | Slice |
|---|---|---|---|---|
| `0007_profiles.py` | `profiles` table, RLS, grants, `handle_new_user()` trigger on `auth.users` | yes | none, table is new | 1 |
| `0008_auth_attempts.py` | `auth_attempts` table, RLS enabled with no `authenticated` grant, grant to `supabase_auth_admin` | yes | none | 1 |
| `0009_auth_hooks.py` | Two Postgres functions, `hook_password_verification_attempt` and `hook_before_user_created`, registered as Supabase Auth Hooks | yes (drop functions, unregister) | none | 1 |

Registering a hook in Supabase's dashboard/config is not a migration and is
listed as a task in `04.1`, not here.

## 6. State management

| State | Lives in | Lifetime | Invalidated by |
|---|---|---|---|
| Supabase session | `supabaseClient` (existing, `frontend/src/api/lib/supabaseClient.ts`) | Until sign-out or token expiry, refreshed by the SDK | Sign-out, password change (`updateUser` revokes other sessions) |
| `me` (username, email) | New `AuthStore`, `frontend/src/stores/AuthStore.ts` | Session lifetime, fetched once on app load | Sign-out clears it; a future username-change re-fetches it |

## 7. Error handling

Split mode. Lives in each sub-plan.

## 8. Test plan

End-to-end cases spanning slices. Each sub-plan carries its own narrower
cases.

| id | Level | Case | Covers |
|---|---|---|---|
| T-X.1 | e2e | A signed-out visitor hitting `/records` directly is redirected to `/sign-in`, not shown a records screen with no data | `RequireAuth`, all slices |
| T-X.2 | e2e | After sign-in, `/records` and every other route inside `RequireAuth` render normally, matching 001's existing behaviour once a session exists | `RequireAuth`, closes 001's outstanding sign-in gap |

## 9. Rollout

| Item | Decision |
|---|---|
| Feature flag | None. Auth is not optional once it ships; 001 has no working product without it |
| Rollout stages | Slice 1 first, alone, since it is what unblocks 001. 2 and 3 ship independently after |
| Kill switch | None meaningful: reverting means restoring the console workaround, which is a deploy, not a flag |
| Metrics to watch | PRD §8: signup completion, sign-in success, password-reset completion, support contacts |
| Rollback plan | Revert the deploy. The `profiles`/`auth_attempts` migrations are additive and safe to leave in place even if the frontend rolls back |

## 10. Task breakdown

Split mode. Each sub-plan carries its own tasks.

## 11. Definition of done

The feature is done when every sub-plan is done and:

- [ ] All tasks shipped or explicitly dropped in the dev log.
- [ ] Test plan cases pass, including T-X.1 and T-X.2 above.
- [ ] Implementation matches the approved design, or a change record explains why not.
- [ ] Observability in place for the metrics named in the PRD.
- [ ] `index.md` updated to `shipped`.
- [ ] 001's `index.md` entry no longer names the console workaround.

## Change log

| Date | Change | Why | Approved by | Sub-plans re-opened |
|---|---|---|---|---|
| 2026-09-14 | Created, split into 3 slices. Slice 1 drafted alongside this index; slices 2 and 3 queued | Build plan approved, all §10 questions answered | pending | — |
| 2026-09-14 | Index and slice 1 approved. Slices 2 and 3 drafted | User approved, asked for slices 2 and 3 | user | — |
| 2026-09-27 | Slice 4 added, `04.4-session-expiry.md`, for FR-23 and FR-24 (AD-8). No shared contract changed | PRD FR-23, FR-24 added | user, 2026-09-27: "approved" | — |
