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
| 000 | [AI Gateway and Usage](./000-ai-gateway/) | P0, platform | 5 Dev | slices 1, 2 and 3 built, CI green, billing re-linked (RPD 10,000 confirmed) | A billing budget alert at a real spend threshold (Tier 1's built-in 250 USD cap is not an alert). Deferred: Docker (D-1), a real database for integration tests in CI, Langfuse (not needed until epic 001 calls the gateway) | 2026-09-13 |
| 001 | [Capture and Records Foundation](./001-capture-and-records-foundation/) | P0 | 5 Dev | in-review | All four slices shipped and verified. Due-date gap closed (D-43). The five cross-slice DoD cases now checked and recorded, all pass. Not yet marked shipped: PRD §8's metrics, audited honestly, are 3 of 7 covered, 1 partial, 3 real gaps (2 buildable, 1 blocked on epic 002's accounts) — waiting on the user's call for how to close that box. No sign-in screen exists yet anywhere in the product; a dev-only console workaround stands in | 2026-09-14 |
| 002 | [Authentication](./002-authentication/) | P0, blocking | 5 Dev | in-review | All three slices built. Slices 1 and 3 live-verified against the real Supabase project; slice 2 (password reset) verified in a real browser against intercepted Supabase responses, since no project credentials are reachable from the build environment. Two real bugs found and fixed earlier: `me` threw instead of returning `username: null`; Google avatar backfill for pre-existing accounts, user-confirmed working. Manual follow-ups, all needing the user's project access: T-1.4 (register the two Auth Hooks); T-1.13's SMTP/email-template config; T-3.5 (one Google sign-in against an email with an existing manual account, for FR-20's auto-link); T-2.4 and slice 2's end-to-end pass against a real mailbox. One design decision open: `VerifyEmailController`'s wrong-vs-expired OTP, which Supabase does not distinguish | 2026-09-17 |

## Planned

Confirmed in [V1 features](./product/v1-features.md). None has an approved epic
or PRD. **Each has a stage-2 design drawn out of order** on 2026-09-17 at the
user's direction, per [`CLAUDE.md`](./CLAUDE.md) §2 — a starting point for
review, not an approved design, and not buildable. Stages 0 and 1 still have to
be written and approved, and each design re-checked against them. None of these
designs cites an FR, because no FRs exist yet; they cite the V1 intake's
numbered sections instead. Each carries a **dark theme** (§6a) reusing 001's approved palette unchanged; no epic adds a colour token.

| # | Epic | Priority | Depends on | Design drawn | New design work |
|---|---|---|---|---|---|
| [003](./003-reminders-and-notifications/) | Reminders and Notifications | P0 | 001, 002 | [draft](./003-reminders-and-notifications/02-design.md) | Recurrence editor, in-app delivery, notification inbox, **the email language 002 also needs** |
| [004](./004-persistent-memory/) | Persistent Memory | P0 | 001, 002 | [draft](./004-persistent-memory/02-design.md) | **Prose answers with citations** — the first surface where Slashit speaks in sentences. Categories, forget-vs-delete |
| [005](./005-personal-search-and-context/) | Personal Search and Context | P0 | 001, 002, 004 | [draft](./005-personal-search-and-context/02-design.md) | Cross-type results, **the relationship tree** — the first nested structure |
| [006](./006-expenses/) | Expenses | P1 | 001, 002 | [draft](./006-expenses/02-design.md) | Summary aggregate, tabular numerals. Everything else reuses 001 |
| [007](./007-events/) | Events | P1 | 001, 002 | [draft](./007-events/02-design.md) | Day grouping only. **Its Upcoming view collides with 010's** |
| [008](./008-goals-and-projects/) | Goals and Projects | P1 | 001, 002, 005 | [draft](./008-goals-and-projects/02-design.md) | **First hierarchical record.** Derived progress, task-to-project linking |
| [009](./009-notes/) | Notes | P1 | 001, 002 | [draft](./009-notes/02-design.md) | Reading column, text area, **the first unsaved-work guard** |
| [010](./010-daily-control/) | Daily Control | P1 | 001, 002, 003, 006, 007, 008 | [draft](./010-daily-control/02-design.md) | Today, Upcoming, Home. **Changes 001's approved navigation and landing screen** |
| [011](./011-proactive-slashit/) | Proactive Slashit | P2 | 005, 010 | [draft](./011-proactive-slashit/02-design.md) | Suggestion surface with because-lines, per-kind silencing |

### What these designs surfaced, that the roadmap did not have

| # | Finding | Who it lands on |
|---|---|---|
| 1 | **Email has no design language, and 002 already needs one.** T-1.13's OTP template is unowned and undesigned. 003's reminder email establishes the language; whichever ships first should own it, not invent a second style | 002 and 003 |
| 2 | **010 reopens 001.** Three flat rail items become nine in two groups, and Capture stops being the landing screen. That needs a change record against 001's approved design under [`CLAUDE.md`](./CLAUDE.md) §7, and it contradicts 001's stated intent that the command bar is the front door | user, at 010's epic |
| 3 | **007 and 010 draw the same Upcoming surface.** 010's is drawn as superseding 007's. Unresolved, it gets built twice | user, at 007's epic |
| 4 | **004 and 005 overlap at `/search`.** A question routes to prose, a term routes to a list. Where the seam sits is an epic-stage decision, not a design one | user, at 004's epic |
| 5 | **006 reuses semantic colour tokens as categorical ones.** Amber means "command" in 001, not "food". Either add a categorical ramp or accept the overlap deliberately | user, at design review |
| 6 | **007's past-event dimming fails contrast as drawn** (62% opacity). Use a token, not opacity. A real defect in the drawing, recorded rather than quietly fixed | user, at design review |
| 7 | **Dark theme found two more hardcoded-colour defects.** 005's match highlight rendered light-on-light and the matched word vanished; 009's note-card excerpt faded to a white bar across every card. Both fixed in dark, both recorded in their §6a. Same class as finding 6 | fixed; light-mode halves still open |
| 8 | **Email does not go dark, in any theme.** Clients rewrite colours and a half-applied dark template is worse than none. The reminder email keeps its light palette on a dark page; whoever owns 002's OTP template inherits the rule | 002 and 003 |

## Shipped

| # | Feature | Shipped | Dev log |
|---|---|---|---|
| — | — | — | — |
