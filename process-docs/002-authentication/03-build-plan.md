---
doc: build-plan
feature: 002-authentication
title: Authentication
stage: 3
status: approved
owner: user
created: 2026-09-14
updated: 2026-09-19
approved_on: 2026-09-14
supersedes: null
---

# Build Plan (HLD) — Authentication

> **Approved** by @user on 2026-09-14. Locked — changes require a change record (§7).

Context: [PRD](./01-prd.md) · [Design](./02-design.md) · [Tech stack](../tech-stack.md)

This document locks the high-level architecture. Section 10 is answered.

## Tables touched

| Table | Change |
|---|---|
| `profiles` | new |
| `auth_attempts` | new |

## 1. Architecture summary

Almost none of this feature is our backend. Per `tech-stack.md` §2, the browser
talks to Supabase Auth directly for every auth action: sign up, sign in,
Google, and password reset are all Supabase JS SDK calls, not GraphQL.
Our own work is two Postgres pieces (a `profiles` table for username, and an
`auth_attempts` table for the lockouts FR-17 to FR-19 require), two Supabase
Auth Hooks that read and write it, Supabase configuration (Google provider,
Resend as SMTP, OTP-not-link email templates), and one Procrastinate job that
purges unverified accounts after 24 hours (FR-8).

Verified against current Supabase documentation while drafting this (sources
in §9 and §10): FR-20's merge is Supabase's own default behavior, no code
needed. FR-17 and FR-19's lockouts have a real, documented hook each. FR-18
does not: nothing in Supabase's hook surface fires on an OTP-code check, so
that one lockout needs a real architecture choice, asked as Q1 in §10.

## 2. Component map

| Component | Responsibility | Talks to | New or existing |
|---|---|---|---|
| `frontend/src/features/auth/` | Sign up, Verify email, Sign in, Forgot password, Reset password screens per `02-design.md` | Supabase Auth JS SDK directly, not GraphQL | New |
| Supabase Auth (managed) | Credential storage, OTP issue and check, Google OAuth exchange, session/JWT issue | Resend (SMTP), Google (OAuth), Postgres | Existing (already the locked provider), newly configured |
| `public.profiles` (Postgres) | Username, unique, one row per `auth.users` row | Written by a trigger on `auth.users` insert | New table |
| `public.auth_attempts` (Postgres) | Failed sign-in and signup counts, lockout windows (FR-17, FR-19). FR-18 has no row here, per Q1 | Written by two Auth Hooks | New table |
| Auth Hook, Password Verification Attempt | Rejects a sign-in past FR-17's threshold, after Supabase itself checks the password | `auth_attempts`, called by Supabase Auth | New, Postgres function |
| Auth Hook, Before User Created | Rejects a signup past FR-19's threshold | `auth_attempts`, called by Supabase Auth | New, Postgres function |
| `app/domains/identity/` (extended) | `me` query returns username alongside 001's timezone | GraphQL, `profiles` | Existing, extended |
| Procrastinate job, `purge_unverified_accounts` | Deletes an account 24h after signup if never verified (FR-8) | `auth.users` via the service-role key | New |

```
Browser --Supabase JS SDK--> Supabase Auth --SMTP--> Resend
                                 |--OAuth-->  Google (auto-linked if the email matches, FR-20)
                                 |--INSERT auth.users--> trigger --> profiles
                                 |--sign-in--> Password Verification Attempt hook --> auth_attempts
                                 |--signup--> Before User Created hook --> auth_attempts
Browser --GraphQL "me"--> identity domain --SQL--> profiles (username), auth.users (email)
Procrastinate (periodic) --service-role--> auth.users (delete unverified, >24h)
```

No GraphQL mutation exists for signup, verification, sign-in, Google, or
reset. Every auth action is client-direct to Supabase.

## 3. Data model

| Entity | Key fields | Owns | Lifecycle | Tenancy scope |
|---|---|---|---|---|
| `profiles` | `id` (PK, FK to `auth.users.id`), `username` (unique, case-insensitive index), `created_at` | `identity` | Created by a trigger, `handle_new_user()`, immediately after `auth.users` gets a row; reads `raw_user_meta_data->>'username'` passed at signup | RLS on `id = auth.uid()` |
| `auth_attempts` | `id`, `subject` (email or `user_id`, whichever the check runs against), `kind` (`sign_in`, `signup`), `failed_count`, `window_started_at`, `locked_until` (nullable) | `identity` | One row per subject per kind, written by the two Auth Hooks in §2, inside Supabase's own request, not ours. No `code` kind: FR-18 relies on Supabase's native rate limit alone, per Q1 | RLS enabled per T2, but no policy grants `authenticated` access; only the hook functions reach it, running with elevated privilege, see AD-3 |

Migrations required: yes. Two new tables, one trigger function, RLS and grants
on both per T2 and the grant rule in `tech-stack.md` §3.

`profiles` is not the mirrored `users` table AD-9 (in `000-ai-gateway`)
rejects: it holds one field `auth.users` cannot, not a copy of identity or
credentials. `auth.users` stays the only credential store.

## 4. API surface

| Endpoint or action | Method | Auth | Input | Output | Serves |
|---|---|---|---|---|---|
| `supabase.auth.signUp` | SDK | none | email, password, `data.username` | session (unconfirmed) | FR-1 to FR-3 |
| `supabase.auth.verifyOtp` | SDK | none (holds the signup session) | email, token | session (confirmed) | FR-4 to FR-7. FR-18's lockout is Supabase's native per-IP limit only, by decision (§10 Q1) |
| `supabase.auth.resend` | SDK | none | email, type `signup` | — | FR-7 |
| `supabase.auth.signInWithPassword` | SDK | none | email, password | session | FR-9 to FR-11 |
| `supabase.auth.signInWithOAuth('google')` | SDK | none | — (redirect) | session, auto-linked to a matching verified account (FR-20) | FR-15, FR-16, FR-20 |
| `supabase.auth.resetPasswordForEmail` | SDK | none | email | — | FR-12 |
| `supabase.auth.updateUser` | SDK | reset-flow session | new password | — | FR-13, FR-14 |
| `me` | GraphQL query | session | — | `username`, `email`, `timezone` | Profile display, extends 001 |

## 5. Model and vendor choices

Not applicable. No model call exists anywhere in this feature.

| Use | Choice | Why | Fallback | Est. cost per call | Latency budget |
|---|---|---|---|---|---|
| Transactional email | Resend, via Supabase Auth's SMTP setting | Already the locked vendor, `tech-stack.md` §1 | None planned; Supabase's built-in sender is not production-suited (this is what epic Q3 asked and found already answered) | 0 USD at V1 volume, `tech-stack.md` §5 | Best-effort, under 30s typical |

## 6. Cross-cutting concerns

| Concern | Decision |
|---|---|
| Authentication | Supabase Auth is the sole identity provider. The browser holds its own session; GraphQL requests carry it as a Bearer JWT, and resolvers apply `000-ai-gateway`'s AD-7 `SET LOCAL` pattern to reach Postgres as the caller |
| Authorisation | One account per user, no roles. `profiles` and `auth_attempts` are both RLS-scoped to the caller |
| Tenant isolation | Identical model to 001: every row carries an owner, RLS enforces it, T7's cross-tenant test applies to `profiles` too |
| Rate limits and quotas | FR-17 (sign-in) and FR-19 (signup) enforce their 5-attempt/15-minute and 5-per-hour numbers through Supabase's Password Verification Attempt and Before User Created hooks, both against `auth_attempts`. FR-18 (code check) has no such hook in Supabase Auth; by decision (Q1), it relies on Supabase's native per-IP limit on `/auth/v1/verify` (30 requests/5 min) alone. Supabase's own IP-based auth rate limits stay on underneath everywhere, as a second layer |
| Cost controls | No model calls. Resend and Google OAuth are both free at V1 volume, per `tech-stack.md` §5 |
| Caching | None. Auth responses are never cached, client or server |
| Observability | Failed sign-in and code attempts are logged (subject, kind, timestamp), never the password or code itself. Kept separate from the LLM usage/analytics tables T6 already walls off, since this is a security log, not prompt content |
| Failure and retry | Every Supabase SDK call failure maps to one of `02-design.md`'s error states. Resend delivery failures surface as the resend cooldown expiring without a code arriving; no automatic backend retry |
| Data retention and privacy | Unverified accounts are deleted 24h after signup (FR-8), by the Procrastinate job. `auth_attempts` rows older than 24h are safe to prune on the same schedule; exact retention is an implementation detail, not a product decision |

## 7. Alternatives considered

| Decision | Chosen | Alternatives | Why they lost | Reversibility |
|---|---|---|---|---|
| Where username lives | `profiles` table, unique indexed | `raw_user_meta_data` on `auth.users` only | No first-class unique constraint, and reading another user's metadata needs the Admin API rather than a normal RLS-scoped query | costly, would need a backfill |
| How the browser reaches Auth | Direct Supabase SDK calls | Proxy every auth call through our own GraphQL mutations | Adds a resolver for every action Supabase already exposes, for no isolation gain since Auth is already outside the GraphQL boundary by design (`tech-stack.md` §2) | cheap, can add a mutation later for one action without moving the rest |
| Unverified-account purge | Procrastinate periodic job | A Postgres `pg_cron` job | Would be a second scheduling mechanism next to the one `tech-stack.md` already locked for background jobs | cheap |
| Sign-in and signup lockout mechanism | Supabase Auth Hooks (Password Verification Attempt, Before User Created), Postgres functions | A GraphQL mutation proxying these two actions | The hooks are Supabase's own documented mechanism for exactly this, and keep the client-direct model AD-2 states | cheap, hooks can be replaced by a proxy later without moving the frontend |
| Code-check lockout (FR-18) | Accept Supabase's native per-IP `/verify` limit alone, no per-account lockout | Reimplement OTP issuance and checking as our own domain, outside Supabase Auth | A real scope increase, moving a working Supabase feature into code we would own and secure ourselves, to close a gap Supabase's own rate limit already narrows | cheap either way; the alternative can still be built later if abuse is observed |

## 8. Architecture decisions to lock

| # | Decision | Status | Graduates to tech-stack.md or product.md |
|---|---|---|---|
| AD-1 | Username lives in `public.profiles`, written by a trigger on `auth.users` insert, never in `raw_user_meta_data` alone | proposed | no |
| AD-2 | The frontend calls Supabase Auth directly for every action in §4, with no GraphQL proxy anywhere, including code-check (Q1 answered). **Amended 2026-09-19: one exception.** Sign-in is now proxied through a `signIn` GraphQL mutation, since AD-7's hook turned out unavailable and enforcing FR-17 honestly requires the server to own the password check (see AD-7) | amended | no |
| AD-3 | `auth_attempts` (§3) holds `sign_in` and `signup` rows, written by the two Auth Hooks. No `code` kind exists: FR-18 relies on Supabase's native rate limit alone (Q1). **Amended 2026-09-19:** `sign_in` rows are now written by the app (`identity.SqlAuthAttemptRepository`), not a hook, and keyed by email rather than user id | amended | no |
| AD-4 | Unverified accounts purge 24h after signup via a Procrastinate periodic task | proposed | no |
| AD-5 | Resend is wired in as Supabase Auth's SMTP provider, not a second, separate email code path | proposed | no |
| AD-6 | FR-20 needs no code: Supabase Auth's automatic identity linking merges a Google sign-in into a matching, already-verified manual account by default | proposed | no |
| AD-7 | FR-17 and FR-19 are enforced by the Password Verification Attempt and Before User Created Auth Hooks, both Postgres functions against `auth_attempts`. **Amended 2026-09-19: FR-17 only.** The Password Verification Attempt hook is Teams/Enterprise only (confirmed against the live project's dashboard, which offers just Send SMS, Send Email, Custom Access Token, Before User Created). FR-17's lockout moves into the app: `identity.SignInInteractor` calls Supabase's Auth REST API directly (`identity.SupabaseAuthService`) instead of the frontend calling `signInWithPassword`, and counts attempts itself before/after. FR-19 is untouched: Before User Created is available and stays registered | amended | no |

## 9. Risks

| Risk | Impact | Mitigation | Trigger to revisit |
|---|---|---|---|
| No Supabase Auth Hook fires on an OTP code check (source: [Auth Hooks](https://supabase.com/docs/guides/auth/auth-hooks)). Per Q1's answer, FR-18 is protected only by Supabase's native per-IP limit on `/auth/v1/verify`, 30 requests/5 minutes (source: [Rate limits](https://supabase.com/docs/guides/auth/rate-limits)), accepted as sufficient for V1 | low, accepted | None beyond the native limit; revisit only if abuse is observed | Abuse observed against `/verify` in production |
| `auth_attempts` grows unbounded without the pruning noted in §6 | low | Slightly larger table, no correctness issue | Add pruning to the Procrastinate job if it is ever missed |

## 10. Questions for the user

Answer before approval. Group by theme, state the recommendation.

Resolved while drafting, sourced, no longer asked: FR-17 and FR-19's lockouts
use the [Password Verification Attempt](https://supabase.com/docs/guides/auth/auth-hooks/password-verification-hook)
and [Before User Created](https://supabase.com/docs/guides/auth/auth-hooks/before-user-created-hook)
hooks (AD-7). FR-20's merge is Supabase's own [automatic identity linking](https://supabase.com/docs/guides/auth/auth-identity-linking),
on by default for a verified email match (AD-6).

| # | Question | Options | Recommendation | Answer |
|---|---|---|---|---|
| ~~Q1~~ | FR-18's code-check lockout has no matching Auth Hook (confirmed against current docs, §9). How should it be enforced? | (a) Move `verifyOtp` for signup verification and password reset behind our own OTP implementation: we generate, send via Resend, store hashed, and check the code ourselves in a GraphQL mutation, fully replacing Supabase's OTP for these two flows. (b) Keep `verifyOtp` as is and accept Supabase's native per-IP limit (30 requests/5 min on `/auth/v1/verify`) as FR-18's only protection, with no per-account lockout | (b). Option (a) is a real scope increase — rebuilding a working, already-configured Supabase feature — to close a gap that Supabase's own rate limit already narrows substantially. Revisit only if abuse is observed | **Answered 2026-09-14.** (b), accept Supabase's native limit |
| ~~Q2~~ | `02-design.md` Q2, the exact `aria-label`/`aria-live` wording for the code boxes and resend action, is still open | Supply a standard convention (`aria-label="Digit N of 6"`, `aria-live="polite"` on the resend row) and move on, or wait for exact copy | Supply the standard convention now; it is cheap to change later and does not affect this document's architecture | **Answered 2026-09-14.** Recommendation adopted, standard convention |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-14 | Created | Drafted after design approval; epic Q3 and PRD Q3 (custom SMTP) turned out already answered by `tech-stack.md` while reading it for this document | pending |
| 2026-09-14 | Verified against current Supabase documentation: FR-17 and FR-19 get a real Auth Hook each (AD-7), FR-20's merge is Supabase's own default (AD-6). Former Q1/Q2 hedges resolved and removed; Q1 rewritten to the one real gap, FR-18's code-check lockout, with a recommendation to accept it rather than rebuild Supabase's OTP. Component map, data model, API surface, cross-cutting concerns, alternatives and risks updated to match | User provided a Google OAuth reference sketch; verified the specifics against Supabase's docs rather than taking either the sketch or the original hedged questions at face value | user |
| 2026-09-14 | Q1 answered: accept Supabase's native per-IP limit for FR-18, no custom OTP. Q2 answered: the recommended `aria-label`/`aria-live` convention stands. `auth_attempts` no longer carries a `code` kind; component map, data model, API surface, cross-cutting, alternatives, risks and AD-2/AD-3 updated to match | User accepted the recommendation for Q1 | user |
| 2026-09-14 | Approved | User approved, proceed to implementation plan | user |
| 2026-09-19 | AD-2, AD-3 and AD-7 amended: the Password Verification Attempt hook (FR-17) is Teams/Enterprise only, confirmed against the live project's dashboard. FR-17's lockout moves into the app: a new `signIn` GraphQL mutation (the one exception to AD-2's direct-client rule) calls Supabase's Auth REST API server-side and enforces the lock via `auth_attempts`, now written by the app rather than a hook, keyed by email. `04.1-manual-signup-and-signin.md` and `05-dev-log.md` carry the implementation detail. FR-19 (Before User Created) is unaffected | User confirmed the hook is missing from their dashboard, then chose the backend-proxy shape over a client-reported-outcome alternative that could not be trusted (a malicious client could always skip the report) | user |
