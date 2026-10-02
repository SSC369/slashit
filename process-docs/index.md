# Feature Registry

Every feature, its current gate, and where it stands. Updated in the same commit
as any stage change.

Product context: [product](./product/product.md) ·
[V1 features](./product/v1-features.md) ·
[tech stack](./tech-stack.md) ·
[V1 intake](./product/intake/2026-09-08-personal-jarvis-v1.md)

Code rulesets, binding once a feature reaches stage 5:
[backend](../backend/.claude/rules/repo-rules.md) ·
[frontend](../frontend/rules/repo-rules.md)

Settled: named Slashit, web, one account per user, commands-only capture, in-app
and email notifications, no charging in V1, no deadline. The stack, auth and
model provider are in [the tech stack](./tech-stack.md).

## Legend

| Stage | Meaning |
|---|---|
| 0 Epic | Feature argued out: requirements, pros, cons, alternatives |
| 1 PRD | Requirements locked |
| 2 Design | Screens and design system in progress or fixed |
| 3 Build plan | HLD drafted or locked |
| 4 Implementation plan | LLD drafted or approved |
| 5 Dev | Building |
| Shipped | Live, dev log closed |

Status values: `draft`, `in-review`, `approved`, `blocked`, `shipped`,
`superseded`.

## Active

| # | Feature | Priority | Stage | Status | Waiting on | Updated |
|---|---|---|---|---|---|---|
| 000 | [AI Gateway and Usage](./000-ai-gateway/) | P0, platform | 5 Dev | slices 1, 2 and 3 built, CI green, billing re-linked (RPD 10,000 confirmed), billing budget alert set (₹100) | T-X.1, the last of the five cross-slice cases (04-implementation-plan.md §8): needs a gateway-backed GraphQL field, which doesn't exist until epic 001 builds a domain that calls the gateway. Deferred: Docker (D-1), a real database for integration tests in CI, Langfuse (not needed until epic 001 calls the gateway) | 2026-09-19 |
| 001 | [Capture and Records Foundation](./001-capture-and-records-foundation/) | P0 | 5 Dev | in-review | All four slices shipped and verified. Due-date gap closed (D-43). The five cross-slice DoD cases now checked and recorded, all pass. PRD §8's metrics: 6 of 7 now covered (soft-delete audit trail and the two FR-9/records-view events closed 2026-09-19). Not yet marked shipped: week-four cohort retention is still blocked on epic 002's accounts. New backend/frontend integration tests added for this change are type/lint-checked only, not run against a live database or browser. The sign-in screen this row once flagged as missing was built in epic 002's slice 1 | 2026-09-19 |
| 002 | [Authentication](./002-authentication/) | P0, blocking | 5 Dev | in-review | All three slices built. Slices 1 and 3 live-verified against the real Supabase project; slice 2 (password reset) verified in a real browser against intercepted Supabase responses, since no project credentials are reachable from the build environment. Two real bugs found and fixed earlier: `me` threw instead of returning `username: null`; Google avatar backfill for pre-existing accounts, user-confirmed working. T-1.13 (SMTP + OTP email template) and T-1.4 (Before User Created hook) done, user-confirmed 2026-09-19. **AD-7 amended the same day:** the Password Verification Attempt hook is Teams/Enterprise only — FR-17's lockout moved into the app (new `signIn` mutation, `identity.SignInInteractor`), not yet live-verified. Manual follow-ups still needing the user's project access: T-1.10 live verification of the new sign-in path; T-3.5 (one Google sign-in against an email with an existing manual account, for FR-20's auto-link); T-2.4 and slice 2's end-to-end pass against a real mailbox, now unblocked by T-1.13. One design decision open: `VerifyEmailController`'s wrong-vs-expired OTP, which Supabase does not distinguish. **Change 2026-09-27:** FR-23, FR-24 (automatic sign-out on an expired or rejected session) added to the PRD; design, AD-8 and sub-plan `04.4-session-expiry.md` drafted, approved 2026-09-27 and built; live check passed, return-after-sign-in owed | 2026-09-27 |
| 006 | [Expenses](./006-expenses/) | P1 | 5 Dev | in progress | Plan index and sub-plan 4.1 approved 2026-10-02. Slice 1 building. Evaluation sets in `backend/tests/eval/`. Migrations `0037` to `0039` collide with 007's local numbers; whichever merges second renumbers | 2026-10-02 |
| 007 | [Events](./007-events/) | P1 | 5 Dev | in progress | Slice 1 merged to `main` 2026-10-02 (`fb0a767`): T-1.1 to T-1.12 done, 327 frontend tests pass, backend passes but for 8 failures not caused by the slice ([dev log](./007-events/05-dev-log.md)). T-1.13 done: NFR-2 98.3%; NFR-1 now measured at the saving card (PRD change), passes; D-15 fixes invented midnight starts. T-1.14 run in dark: B-1 to B-6, one defect (first command after load dropped). **Next:** X-1, any number of alerts per event (user, 2026-10-02): change records on epic and PRD, then design, build plan and index, before 4.2. Owed: decisions on B-1 to B-5, light-theme pass, review of the 60-line set and of D-1 to D-14. Migrations `0037`, `0038` now on `main`, so 006 renumbers. 4.2 drafted after X-1 | 2026-10-02 |

## Planned

Confirmed in [V1 features](./product/v1-features.md), not yet opened.

| # | Epic | Priority | Depends on |
|---|---|---|---|
| 008 | Goals and Projects | P1 | 001, 002, 005 |
| 009 | Notes | P1 | 001, 002 |
| 010 | Daily Control | P1 | 001, 002, 003, 006, 007, 008 |
| 011 | Proactive Slashit | P2 | 005, 010 |
| 012 | Production Readiness | P0 | all shipped epics |

Epic 012 opens last, once the others are shipped, so its argument covers what
they actually built rather than a guess made now. One sub-plan is confirmed by
the user: integrate Resend for real (a verified sending domain,
`RESEND_API_KEY`, `REMINDER_EMAIL_FROM`) and test every reminder email path end
to end, closing 003's T-3.10. A second, from epic 006's Q7 on 2026-10-02: convert a
foreign-currency expense to ₹ on capture, storing the ₹ value only, once the
user configures an exchange-rate source. Until then 006 refuses non-rupee
amounts.

> Assumption: scope beyond email is not yet supplied. Argued in full at epic
> 012's own stage 0, when it opens.

## Shipped

| # | Feature | Shipped | Dev log |
|---|---|---|---|
| 003 | [Reminders and Notifications](./003-reminders-and-notifications/) | 2026-09-27, desktop and dark only. Mobile deferred (D-31), not built; tracked as a future task, not part of this feature | [05-dev-log.md](./003-reminders-and-notifications/05-dev-log.md) |
| 004 | [Persistent Memory](./004-persistent-memory/) | 2026-09-27, desktop only. NFR-4 and NFR-5 re-measured after deploy (epic 012); mobile deferred with 003's D-31; backup window at launch | [05-dev-log.md](./004-persistent-memory/05-dev-log.md) |
| 005 | [Personal Search and Context](./005-personal-search-and-context/) | 2026-10-02. Records embedded as documents, searches as queries (D-22): every database needs a one-off re-embed at deploy. NFR-4's question latency missed, accepted for V1 | [05-dev-log.md](./005-personal-search-and-context/05-dev-log.md) |
