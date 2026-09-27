---
doc: prd
feature: 002-authentication
title: Authentication
stage: 1
status: approved
owner: user
created: 2026-09-14
updated: 2026-09-27
approved_on: 2026-09-14
supersedes: null
---

# Epic PRD — Authentication

> **Approved** by @user on 2026-09-14. Locked — changes require a change record (§7).

Context: [Epic](./00-epic.md) · [Product](../product/product.md)

## 1. Problem

No real person can create or reach an account in Slashit today. Every session
so far starts from a developer-only workaround, recorded in `index.md` as the
reason epic 001 is still `in-review`. Every record in the product is scoped to
one owner; nothing built can be used by anyone but its own developers until an
account can be created and returned to without help.

## 2. Users and jobs

| User | Job to be done | Today's workaround |
|---|---|---|
| New user | Create an account and prove they own the email they signed up with | None. Only a developer can open a session |
| Returning user | Sign back in and reach their own data | Same developer-only workaround |
| Locked-out user | Recover access after forgetting a password | None |

## 3. Goals

| # | Goal | What we measure |
|---|---|---|
| G1 | Signup completes without support help | Share of started signups that reach a verified account |
| G2 | A returning user reaches their account without friction | Sign-in success rate |
| G3 | A forgotten password does not strand the user | Password-reset completion rate |

> Assumption: no numeric targets, following the decision recorded in 001's PRD
> §3 on 2026-09-08 — V1 has no users, so a target now would be invented. Each
> goal is instrumented from day one and a target is set once real usage exists.

## 4. Non-goals

- Social login beyond Google. No GitHub, Apple or other identity providers in
  this feature.
- Multi-factor authentication beyond the email code used to verify signup and
  to authorize a password reset.
- Teams, invites, shared or multi-user accounts.
- Profile or settings management beyond the fields signup collects.
- Any product record type. Those belong to epics 003 to 011, which all depend
  on this one.

## 5. User stories

- **US-1.** As a new user, I sign up with a username, an email and a password,
  so that I have an account of my own.
- **US-2.** As a new user, I verify my email with a code sent to me, so that my
  account is confirmed as mine before I can use it.
- **US-3.** As a returning user, I sign in with my email and password, so that
  I reach my own data.
- **US-4.** As a user who forgot their password, I request a reset and prove I
  own the email, so that I can set a new password and get back in.
- **US-5.** As a user waiting on a code, I can ask for it to be resent, so a
  lost or delayed email does not strand me.
- **US-6.** As a new or returning user, I sign up or sign in with Google
  instead, so that I skip the password and the email code entirely.
- **US-7.** As a user, repeated wrong attempts against my account (bad
  passwords, bad codes) or repeated signups from one source are throttled, so
  my account and the signup path cannot be brute-forced or abused.
- **US-8.** As a signed-in user, I end my session from wherever the app shows
  my account, so a shared or public device does not stay signed in as me.
- **US-9.** As a signed-in user whose session has expired or been revoked, I
  am signed out and told why, so I never act on a screen that silently
  fails and no one else sees my data after me.

## 6. Functional requirements

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-1 | A person creates an account with a username, an email and a password | must | US-1 |
| FR-2 | Signup fails with a field-level error when the email is already registered, the username is taken, or a field fails validation | must | US-1 |
| FR-3 | Username uniqueness is case-insensitive; usernames are 3 to 20 characters, letters, numbers and underscore only | must | US-1 |
| FR-4 | After signup, a one-time numeric code is sent to the entered email | must | US-2 |
| FR-5 | An account cannot sign in until its code is entered correctly | must | US-2 |
| FR-6 | An incorrect code and an expired code produce distinct errors | must | US-2 |
| FR-7 | A user can request the code be resent, subject to a cooldown between requests | should | US-5 |
| FR-8 | An account not verified within 24 hours of signup is removed, and its email becomes available for a new signup | must | US-2 |
| FR-9 | A verified user signs in with email and password and reaches an authenticated session | must | US-3 |
| FR-10 | Sign-in on an unverified account routes back to verification instead of a generic failure | must | US-3 |
| FR-11 | Sign-in with a wrong password and sign-in with an unregistered email produce the identical error message | must | US-3 |
| FR-12 | A user requests a password reset by entering their email | must | US-4 |
| FR-13 | A password reset completes only after a one-time code proves email ownership, then a new password is set | must | US-4 |
| FR-14 | A requested but uncompleted password reset expires and can no longer set a password | must | US-4 |
| FR-15 | A person creates an account, or signs in to an existing one, using Google instead of a username, email and password | must | US-6 |
| FR-16 | An account created or accessed through Google is treated as email-verified; it never sees the code screen | must | US-6 |
| FR-17 | After 5 consecutive failed sign-in attempts on one account, further attempts on it are blocked for 15 minutes | must | US-7 |
| FR-18 | After 5 consecutive wrong verification or reset codes, that code is blocked and a new one must be requested | must | US-7 |
| FR-19 | Signup attempts from the same email or address are rate-limited | should | US-7 |
| FR-20 | A Google sign-in whose email matches an existing manually-created account signs into that account, rather than creating a second one | must | US-6 |
| FR-21 | A Google sign-in's avatar, when Google provides one, is stored and shown wherever the app already shows the account | should | US-6 |
| FR-22 | A signed-in user can end their session from wherever the app shows their account | must | US-8 |
| FR-23 | When the app's server rejects the session, or the session can no longer be renewed, the user is signed out, lands on sign-in with a notice saying the session expired, and returns to the page they were on after signing in | must | US-9 |
| FR-24 | After any sign-out, nothing from the ended session remains held or shown in the app | must | US-8, US-9 |

> Confirmed 2026-09-14 (Q7, Q8): FR-20's merge behavior and the 5-attempt /
> 15-minute / 5-per-hour numbers in FR-17 to FR-19 and NFR-6 to NFR-8, all
> originally drafted as defaults, now stand as given.

## 7. Non-functional requirements

| id | Requirement | Number | How it is measured |
|---|---|---|---|
| NFR-1 | Passwords are never stored or logged in plain text | 0 occurrences | Code review |
| NFR-2 | A verification or reset code is single-use | 1 use per code | Test |
| NFR-3 | A verification or reset code expires | ≤ 15 minutes from issue | Test |
| NFR-4 | Resend of a verification or reset code is rate-limited | ≤ 1 request per 30s per account | Test |
| NFR-5 | An authenticated session survives a browser reload | No re-prompt on reload | Test |
| NFR-6 | Sign-in lockout threshold (FR-17) | 5 failed attempts, 15-minute cooldown | Test |
| NFR-7 | Code-attempt lockout threshold (FR-18) | 5 wrong codes, then a new code is required | Test |
| NFR-8 | Signup rate limit per email or address (FR-19) | ≤ 5 signups per hour | Test |

> Assumption: NFR-3's 15 minutes and NFR-4's 30 seconds are reasonable
> defaults, not values the user gave. Confirm or override before the build
> plan; logged as Q6 below.

## 8. Success metrics

Thirty days after launch.

| Metric | Target | Instrumented by |
|---|---|---|
| Signup completion rate | No target yet, see G1 | Signup and verification events |
| Sign-in success rate | No target yet, see G2 | Sign-in attempt events |
| Password-reset completion rate | No target yet, see G3 | Reset-flow events |
| Account-access support contacts | Trend down, no baseline | Support log |

## 9. Dependencies

| Dependency | Type | Owner | Status |
|---|---|---|---|
| An identity and session provider | vendor | tech-stack | Resolved, see `tech-stack.md` |
| Outbound email capable of production signup volume | vendor | tech-stack | Resolved, see `tech-stack.md`. Resend, not Supabase's built-in sender |
| A record-owner identity every other epic keys against | internal | 001 and every epic after it | Not yet available; this feature produces it |
| A Google sign-in integration | vendor | tech-stack | Open. Configuration on the existing identity provider, not a new one, per the epic |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Email provider's rate limit is unsuited to production signup volume | low | high, blocks all new users | Resolved: Resend is the locked provider (`tech-stack.md`), not Supabase's built-in sender |
| Username record drifts out of sync with the identity record | low | med | One transaction on create; addressed in the build plan |
| Verification and reset share a code mechanism, so a bug in one leaks into the other | low | med | Two call sites in the build plan, not one branching function |
| Differing error messages let an attacker enumerate registered emails | low | med | FR-11 requires an identical message |
| A Google sign-in reaches an existing manual account (FR-20) without the user ever having linked the two themselves | low | med, a surprised user | Surface this plainly the first time it happens, in the build plan |
| Sign-in and code fields were unthrottled before this change, a brute-force target | med (pre-existing) | high | FR-17, FR-18, FR-19 close this |

## 11. Open questions

| # | Question | Blocks | Owner | Answer |
|---|---|---|---|---|
| ~~Q3~~ | Is custom SMTP needed for V1 launch, or can Supabase's default wait? | build plan | user, tech-stack | **Answered.** Resend is already the locked email vendor in `tech-stack.md`; the question did not need a new decision |
| Q6 | Are the 15-minute code expiry and 30-second resend cooldown (NFR-3, NFR-4) acceptable, or should they be different? | build plan | user | Open |
| ~~Q7~~ | Does a Google sign-in on an email with an existing manual account merge with it, or get refused? | build plan | user | **Answered 2026-09-14.** Merges with it. FR-20 added. |
| ~~Q8~~ | Are the 5-attempt / 15-minute lockout and 5-per-hour signup limit (NFR-6 to NFR-8) acceptable, or should they be different? | build plan | user | **Answered 2026-09-14.** The drafted numbers stand. |

## 12. Out of scope

- Social login beyond Google.
- Multi-factor authentication beyond the email code.
- Teams, invites, multi-user accounts.
- Profile or settings management beyond signup fields.
- Any product record type; those are epics 003 to 011.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-14 | Created | Drafted after epic approval and the PRD-blocking questions (Q2, Q4, Q5) were answered | pending |
| 2026-09-14 | Approved | User approved, proceed to design | user |
| 2026-09-14 | Google sign-in added: US-6, FR-15, FR-16 added; Non-goals and Out of scope narrowed from "social/OAuth login" to "social login beyond Google"; a Google dependency and an account-linking risk added; Q7 opened. Rate limiting added: US-7, FR-17 to FR-19, NFR-6 to NFR-8 added; a brute-force risk added; Q8 opened. Q1 dropped, no longer needed | User asked for Google sign-in and rate-limit error cases, and said the radius-app reference is no longer needed | user |
| 2026-09-14 | Q7 answered: FR-20 added, a Google sign-in merges into a matching manual account. Q8 answered: the drafted rate-limit numbers stand. Risk and assumption note updated to match | User answered both build-plan-blocking questions | user |
| 2026-09-15 | FR-21 added: a Google-provided avatar is stored and displayed | User asked for it once told Google sign-in was live but not capturing one | user |
| 2026-09-14 | Q3 answered: Resend was already the locked email vendor in `tech-stack.md`, not Supabase's built-in sender. Dependency and risk rows updated | Found while reading `tech-stack.md` ahead of the build plan | user |
| 2026-09-15 | US-8, FR-22 added: ending a session. Built ahead of this amendment (`AppShell`'s account popover, `05-dev-log.md` T-4.1/T-4.2) since sign-out was a real product gap no approved doc had named, not a new direction to argue | User asked for a sign-out option | user |
| 2026-09-27 | US-9, FR-23, FR-24 added: automatic sign-out on an expired or rejected session, with a notice. Re-opens design (§4 Sign in, §8), build plan (AD-8) and a new sub-plan `04.4-session-expiry.md` | User asked for it after the app kept showing screens that failed with "Not authenticated" | user, 2026-09-27: "approved" |
