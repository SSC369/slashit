---
doc: tech-stack
title: Slashit Technical Stack
status: current
owner: user
created: 2026-09-09
updated: 2026-09-23
---

# Slashit — Technical Stack

The standing technical context every build plan inherits. Read this before
drafting a stage 3 build plan, the way you read
[the product doc](./product/product.md) before a PRD.

This document owns what the stack **is**. Each choice carries the alternatives
it beat, so the reasoning survives without a separate decision folder. When a
choice changes, it changes here, and the change log at the bottom records it.

---

## 1. The stack

| Layer | Choice |
|---|---|
| API medium | GraphQL |
| GraphQL server | Strawberry, mounted on FastAPI |
| API framework | FastAPI |
| Language | Python 3.12 |
| Database | PostgreSQL, hosted by Supabase |
| ORM | SQLAlchemy 2.x, async |
| Database driver | asyncpg |
| Migrations | Alembic |
| Vector search | pgvector, in the same database |
| Auth | Supabase Auth |
| Data isolation | PostgreSQL Row Level Security |
| In-app notification transport | GraphQL subscriptions over WebSockets |
| Background jobs | Procrastinate, backed by PostgreSQL, run by a separate worker container |
| Subscription backplane | PostgreSQL `LISTEN/NOTIFY` |
| Frontend | React, built with Vite |
| Server state | Apollo Client, with MobX stores as the source of truth |
| UI state | MobX |
| Typed client | `graphql-codegen` from the Strawberry schema |
| Components | shadcn/ui |
| Design system | Produced in Claude Design at stage 2 of each feature |
| Repository | Plain folders, `backend/` and `frontend/` |
| Backend hosting | Managed container host. Render or Railway, undecided |
| Frontend hosting | Vercel |
| Email | Resend |
| Model framework | LangChain, `langchain-core` plus `langchain-google-genai` |
| Model provider | Google Gemini Flash, paid tier. `gemini-3.6-flash` in V1 |
| LLM observability | Langfuse |

---

## 2. The Supabase boundary

This rule matters more than any single row above, and it is not optional.

**The browser talks to Supabase for authentication only. Every record read and
write goes through the Strawberry GraphQL endpoint.**

Supabase publishes its own data APIs, PostgREST and `pg_graphql`. Neither is
used. A client that reaches the database directly bypasses the AI gateway, the
per-user usage attribution required by [epic 000](./000-ai-gateway/), and every
business rule the resolvers hold. One door in, and it is ours.

---

## 3. Why each choice

### API medium: GraphQL

Chosen by the user on 2026-09-09.

| Alternative | Why it lost |
|---|---|
| REST with an OpenAPI-generated client | The cheaper path to a typed client, and still a valid one. Rejected by user direction |
| Supabase PostgREST or `pg_graphql` as the API | Bypasses the AI gateway and per-user usage attribution. Puts business rules in database policies, where they are hard to test |

**What it buys.** One typed contract, with `graphql-codegen` generating the
React hooks from the schema. The records surface fetches exactly the fields a
view needs, which suits a product where a task, an expense and a memory carry
different fields. Queries, mutations and subscriptions share one endpoint and
one auth path.

**What it costs.** N+1 queries are GraphQL's default failure mode, so DataLoader
is required from the first resolver rather than retrofitted. HTTP caching by URL
stops working, and caching moves into the client and the resolvers. A
careless or hostile deep query is expensive, so depth and complexity limits are
needed before public launch. Strawberry is a smaller ecosystem than FastAPI's
REST path.

### Database and auth: Supabase

| Alternative | Why it lost |
|---|---|
| Clerk for auth | The best developer experience of the group. It loses on one structural point: identity would live in a third-party system while records live in Slashit's PostgreSQL, kept in step by webhooks. Every missed webhook is a user who can sign in but owns no rows, or a row whose owner does not exist. That failure is silent and it appears in production |
| Auth0 | The same sync problem as Clerk, with more configuration surface than one account per user justifies, and a steeper price curve |
| AWS Cognito | Poor developer experience, and its free-tier structure has changed more than once |
| WorkOS AuthKit | A generous free allowance and the right answer if enterprise SSO were on the roadmap. It is not: teams and sharing are product non-goals |
| Better Auth, self-hosted | Owns its own data, which is attractive. It is TypeScript-first and the backend here is Python |
| Auth built in-house | One account per user makes it look small. Password reset, session revocation, OAuth and breach response are where that impression ends |
| Self-managed PostgreSQL on EC2 | Backups, upgrades, connection limits and pgvector installation all become the operator's job for no gain at this size |

**What it buys.** Identity lives in `auth.users`, in Slashit's own database, so
no synchronisation exists to break. One database serves relational records,
full-text search, semantic search through pgvector, and the job queue. Row Level
Security makes principle 7 of the product doc a database guarantee rather than a
code-review guarantee.

**What it costs.** Auth and the database are now the same vendor, so one outage
takes both. Free-tier projects pause after a period of inactivity, which a
product with real users cannot accept. Migration away is costly: users export,
but password hashes tie the destination to a compatible hashing scheme and OAuth
links generally have to be re-established by the user.

### Background jobs: Procrastinate on PostgreSQL

| Alternative | Why it lost |
|---|---|
| Celery with Redis | Three processes and a second stateful system before a single reminder fires, for a workload measured in dozens of jobs a day |
| Celery without Redis | Celery without a broker is not Celery. The dependency is the point |

**What it costs.** The queue shares a database with user traffic. At this size
that is fine. At ten thousand times this size it is not.

### Hosting: managed containers

| Alternative | Why it lost |
|---|---|
| AWS EC2 free tier | A `t3.micro` is 1 GiB of memory. An API process, a worker, a scheduler, Redis and PostgreSQL do not fit in it under real use. The saving is roughly twenty dollars a month against an operator cost measured in evenings |

**What it costs.** Four vendors instead of one, each a dependency and a bill.
Not free, unlike the EC2 free tier on paper.

### Frontend data layer: Apollo Client, with MobX as the store of record

Chosen by the user on 2026-09-09, replacing TanStack Query.

The objection that decided the original choice still stands and is answered
structurally rather than abandoned. **A normalised cache is a second store of
what the server holds, with its own invalidation rules. Pillar P2 forbids the AI
path and the structured path disagreeing, and a stale cache is precisely that
disagreement.**

So Apollo is used as a transport, not as a cache. MobX stores are the source of
truth for server state. Operations fetch with `network-only`, `InMemoryCache` is
left untuned, and every response is written into a store by the operation's
response handler. There is one store of server data, and the AI path and the
structured path both write into it.

| Alternative | Why it lost |
|---|---|
| TanStack Query over `graphql-request` | The original choice, and a good one. Replaced by user direction |
| Apollo with its normalised cache as the source of truth | The pillar P2 objection above, unanswered. This is the configuration being avoided, not the library |
| urql | Same cache question as Apollo, with a smaller ecosystem and no advantage here |

**What it buys.** One client covers queries, mutations and subscriptions over a
single auth path, so the WebSocket transport of section 1 needs no second
library. A subscription payload writes into the same store method a query calls,
which removes cache reconciliation entirely.

**What it costs.** More code than letting a cache do the work, and a discipline
that has to be enforced rather than assumed: a component reading a query result
directly instead of a store silently reintroduces the second store. The rule is
written down in `frontend/rules/repo-rules.md` section 7.

### Data layer: SQLAlchemy 2.x async, asyncpg, Alembic

Settled by [epic 000's build plan](./000-ai-gateway/03-build-plan.md) on
2026-09-12, decisions AD-3 to AD-6. No row existed for any of these before, and
they block every backend file.

| Alternative | Why it lost |
|---|---|
| SQLModel instead of SQLAlchemy | Thinner, and by FastAPI's author. It lags SQLAlchemy on async and on complex queries, and the backend has a repository layer that wants full query power |
| Raw asyncpg, no ORM | Fast, but every repository hand-rolls its mapping and Alembic has nothing to read |
| psycopg3 instead of asyncpg | Both work. asyncpg is faster and is what SQLAlchemy's async documentation assumes |
| Supabase CLI SQL migrations instead of Alembic | Attractive, because Row Level Security policies are SQL. Two migration histories over one database is the problem it appears to solve. Alembic runs raw SQL for policies |

**Python 3.12**, not 3.13, because the ecosystem lag on a new minor version buys
nothing here.

### Identity on the connection, answering T-Q2

Settled by [epic 000's build plan](./000-ai-gateway/03-build-plan.md) on
2026-09-12, decision AD-7.

**Two statements inside the transaction that does the work, in this order:**

```sql
SELECT set_config('request.jwt.claims', '{"sub":"<user_id>"}', true);
SET LOCAL ROLE authenticated;
```

Both are `LOCAL`, so neither survives the transaction and a pooled connection
cannot carry one user's identity into the next request. This is why a model
call's usage row is written in the caller's transaction rather than its own.

**The role switch is not optional, and omitting it leaks every row.** The
application connects as `postgres`, which on Supabase is not a superuser but does
carry `rolbypassrls`. That privilege outranks `FORCE ROW LEVEL SECURITY`, so the
policy is never evaluated and every query returns every user's rows, with no
error. `authenticated` does not carry the privilege. Measured on 2026-09-12
against the live database; the evidence is in
[epic 000 sub-plan 2](./000-ai-gateway/04.2-identity-and-isolation.md) section 6.

Every table therefore also needs `GRANT SELECT, INSERT, UPDATE, DELETE ... TO
authenticated`, because after the switch the connection holds only what that role
is granted. A table created without the grant fails with a permission error
rather than leaking, which is the right way round.

Rule T2 makes Row Level Security a database guarantee. This is the mechanism that
makes the guarantee bind, and getting it wrong disables isolation with no error,
which is why it is written down rather than left to a connection helper.

**There is no mirrored `users` table** (AD-9). Identity lives only in
`auth.users`. A second copy would need synchronising, which is the failure this
document rejected Clerk over.

### Repository: plain folders

Two folders at the repository root, `backend/` and `frontend/`, set by the user
on 2026-09-09. The earlier `apps/api`, `apps/web`, `packages/` layout carried a
`packages/` folder that nothing would fill and an `apps/` level that wrapped two
entries.

Turborepo was the original choice and is deferred. A Python API and one web app
share no TypeScript package, so monorepo tooling has nothing to do yet. The
folder discipline is free, the tooling is not. Add it the day a second
JavaScript app exists.

Each folder owns its own structure and conventions, and neither is restated
here:

| Folder | Ruleset |
|---|---|
| `backend/` | [`backend/.claude/rules/repo-rules.md`](../backend/.claude/rules/repo-rules.md) |
| `frontend/` | [`frontend/rules/repo-rules.md`](../frontend/rules/repo-rules.md) |

### Model framework: LangChain

Chosen by the user on 2026-09-12.

**LangChain sits below the gateway's `ModelProvider` Protocol, never above it.**
Nothing outside `app/domains/gateway/adapters/` imports it. Rule T4 requires the
boundary to be ours; if LangChain types reached a service we would have swapped
our abstraction for theirs and T4 would hold in name only.

| Alternative | Why it lost |
|---|---|
| `google-genai` directly | Fewer layers and simpler error classification. Replaced by user direction |
| `langchain`, the full package | Carries agents, chains and memory. Only `langchain-core` and `langchain-google-genai` are installed for the image |

**What it buys.** `with_structured_output(schema)` enforces the response shape,
which is most of what FR-16 asks for and removes most malformed-result cases.

**What it costs.** LangChain wraps provider exceptions in its own, so telling a
quota error from an outage from a timeout means unwrapping to the underlying
`google-genai` exceptions. The gateway adapter carries more error-mapping code
than a direct SDK call would, not less.

**The wider toolkit is installed but not deployed.** `langchain-community`,
`langchain-chroma`, `sentence-transformers`, `langchain-tavily`,
`langchain-huggingface` and `pypdf` live in `backend/requirements-ai.txt`, which
the image never installs. Together they cost 1.4 GB, most of it PyTorch. A
package graduates into `requirements.txt` when code imports it. Two of them carry
unsettled decisions: Chroma is a second vector store where this document chose
pgvector in one database, and `sentence-transformers` means local embeddings
where this document chose Gemini.

### Model provider: Gemini Flash, paid tier

The provider was settled on 2026-09-08. The tier moved from free to paid on
2026-09-09.

| Alternative | Why it lost |
|---|---|
| The Gemini free tier | Free-tier terms generally permit a provider to use inputs to improve its products. This product holds passports, finances and family details. It also means one shared rate limit, exhaustible by one user, and the saving was around one dollar a month per hundred users |
| A paid tier on another vendor | No reason to move. The gateway boundary keeps this cheap to revisit if Gemini disappoints on quality or price |
| Per-user API keys | Asks a user to obtain a key before capturing anything, which kills the first run |
| Local or self-hosted model | Infrastructure out of proportion to a V1 |

**What it costs.** A billing relationship and a bill that can surprise. The
constraint moves from quota to spend, so a runaway user or a retry loop now
costs money rather than returning an error.

### Live delivery and background work: settled by epic 003

Settled by [epic 003's build plan](./003-reminders-and-notifications/03-build-plan.md)
on 2026-09-23, decisions AD-1, AD-4 and AD-9.

**Subscription backplane: PostgreSQL `LISTEN/NOTIFY`** (AD-4, closes T-Q3). A
process that creates something a user should see live issues `NOTIFY` on one
channel after its transaction commits, with a payload of ids only, never
content. Each API instance holds one listening connection and forwards to that
user's open subscriptions. A client refetches on every reconnect, so a dropped
signal costs latency, never correctness.

| Alternative | Why it lost |
|---|---|
| Redis pub/sub | A second stateful service, which this stack removed on purpose |
| Polling every 30 seconds | Misses epic 003's 5-second live-delivery target and adds constant traffic |

**Worker: a separate container** (AD-9). `procrastinate worker` runs apart from
the API, so a restart or scale-to-zero of the API never stops scheduled work.
It costs a second container, about 7 USD a month, `estimate`.

**One domain per record type** (AD-1). A record type with its own lifecycle gets
its own backend domain; `records` reaches it through a port, as it reaches
reminders. Epics 006 to 009 follow this unless their build plan argues otherwise.

---

## 4. Standing technical rules

Binding on every build plan. A build plan that contradicts one of these says so
explicitly and argues for it.

| # | Rule |
|---|---|
| T1 | One door in. The browser reaches data only through the GraphQL endpoint, never through a Supabase data API |
| T2 | Row Level Security is enabled, with a policy, in the same migration that creates any table holding user data. A table without a policy is a defect, not a default |
| T3 | The service-role key never reaches the browser, and never serves a request made on behalf of a user unless the resolver has already established ownership. It is for migrations and background jobs |
| T4 | The model provider stays behind a boundary. Nothing above it knows which provider is in use, so a tier or vendor change is configuration, not a rewrite |
| T5 | DataLoader from the first resolver, not retrofitted after the N+1 appears |
| T6 | Prompt content never reaches the usage or analytics tables. Passports and finances do not belong in an observability store |
| T7 | Every feature touching user data tests the boundary: a case where user A requests user B's record and receives nothing |
| T8 | Every number in a build plan carries its source. A benchmark, a vendor page, a measurement, or the label `estimate` |

---

## 5. Cost envelope

> `estimate`. Stated from memory on 2026-09-09 and not read from a vendor page.
> See section 7.

| Item | At launch | With real users |
|---|---|---|
| Backend host | 0 to 7 USD | 7 to 20 USD |
| Supabase | 0 USD, free tier | 25 USD, Pro |
| Frontend host | 0 USD | 0 USD |
| Resend | 0 USD | 0 to 20 USD |
| Gemini Flash | under 1 USD | 1 to 5 USD |
| Langfuse | 0 USD | 0 USD |
| **Total** | **about 10 USD a month** | **about 50 to 70 USD a month** |

Model cost per capture is about 0.0001 USD, from 500 tokens in at 0.10 USD per
million and 150 tokens out at 0.40 USD per million. A user capturing 100 times a
month costs about one cent. This is why the free tier was not worth its terms.

---

## 6. Open

| # | Question | Blocks |
|---|---|---|
| T-Q1 | Render or Railway for the backend? | epic 000 build plan |
| ~~T-Q2~~ | How the authenticated user's identity reaches the database connection so RLS applies | **Answered 2026-09-12**, section 3. `SET LOCAL` claims plus `SET LOCAL ROLE authenticated`. Claims alone are not sufficient |
| ~~T-Q3~~ | What backplane carries GraphQL subscriptions when there is more than one API instance? | **Answered 2026-09-23.** PostgreSQL `LISTEN/NOTIFY`, section 3 |
| T-Q4 | What are the query depth and complexity limits, as numbers? | public launch |
| ~~T-Q5~~ | Vercel or Cloudflare Pages for the frontend? | **Answered 2026-09-13.** Vercel |
| T-Q6 | Supabase free-tier projects pause after inactivity. What is the current threshold, and on what date does the project move to Pro? | launch |
| T-Q7 | Does the GraphQL schema stay one graph as epics land, or split by domain? | epic 005 |
| T-Q8 | The model tier moved from free to paid, so a runaway user now costs money rather than exhausting a shared quota. Do epic 000's per-user caps keep request ceilings, or gain a spend ceiling? | epic 000 build plan |

---

## 7. Verification owed

Every price and free-tier limit in this document was stated from memory during
the 2026-09-09 discussion and **none has been checked against a vendor page**.
Confirm Supabase, Render, Railway, Vercel, Cloudflare, Resend and Gemini current
pricing before the first bill, and record each figure with its source, per rule
T8.

Two obligations sit alongside it:

1. **Read Gemini's paid-tier data-handling terms before launch.** Better terms
   than the free tier are the expectation, but expectation is not reading. Open
   as Q10 in the product doc.
2. **Set a provider-side billing alert and spend cap before the first real
   user.** A cap is the only defence that works while nobody is watching.

---

## 8. History

The stack has been revised twice, both times on 2026-09-09.

The original choice put FastAPI, Celery, Celery beat, Redis and PostgreSQL on a
single AWS EC2 instance, assumed a REST API, left the auth provider open, and
used the Gemini free tier. It was made on 2026-09-08, before any build plan
existed, and it was replaced the moment the product was aimed at real users:
operator hours became scarcer than hosting cash, and the free tier's terms
became indefensible for a product holding passports.

FastAPI, PostgreSQL, React, Vite, MobX, shadcn/ui, Resend and Gemini carried
over unchanged. Everything else in the infrastructure layer was replaced.

The second revision was narrower and touched the frontend only: the data layer
moved from TanStack Query to Apollo Client, and the repository layout moved from
`apps/api` and `apps/web` to `backend/` and `frontend/`. Both came from reading
the `radius` codebase, an existing production system on the same patterns, while
drafting the two repository rulesets.

The full original records, and the ones that superseded them, were removed on
2026-09-09 by commit `f8016bd`, when the decision folder was folded into this
document. They are readable at its parent:

```
git show f8016bd^:process-docs/product/decisions/0004-v1-technology-stack-revised.md
```

Seven files sit there: decisions 0001 to 0006 and their README. Decisions 0004,
0005 and 0006 are the ones this document absorbed.

---

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-23 | Subscription backplane set to PostgreSQL `LISTEN/NOTIFY`, closing T-Q3. Background jobs run in a separate worker container. One backend domain per record type. Stale downstream: none; epic 003 is the first consumer | Decisions AD-1, AD-4 and AD-9 of epic 003's approved build plan, graduated per rule 8 of the process | user |
| 2026-09-14 | T-Q3 and T-Q7's `Blocks` column renumbered from epic 002/004 to epic 003/005 | Epic 002, Authentication, inserted ahead of the old 002 to 010, which shifted to 003 to 011 (`product/v1-features.md`, 2026-09-14) | user |
| 2026-09-13 | T-Q5 answered: frontend hosting is Vercel | Epic 001's build plan needed it | user |
| 2026-09-09 | Created, absorbing decision records 0004, 0005 and 0006 | User removed the decisions folder and asked for one technical document | user |
| 2026-09-09 | Server state moved from TanStack Query to Apollo Client. The pillar P2 objection to a normalised cache is preserved by making MobX stores the source of truth and Apollo a transport | User direction while drafting the repository rulesets | user |
| 2026-09-12 | V1 model changed from `gemini-2.5-flash` to `gemini-3.6-flash`. The former returns 404 to new accounts, and Google's error names the latter as its replacement | Discovered by calling the API during epic 000 slice 3 | user |
| 2026-09-12 | Added LangChain as the model framework, below the gateway's provider Protocol. Recorded that the wider AI toolkit is installed locally and not deployed | User direction while planning epic 000 slice 3 | user |
| 2026-09-12 | Corrected the T-Q2 answer. The claim alone leaks every row because `postgres` carries `rolbypassrls`; `SET LOCAL ROLE authenticated` is mandatory alongside it. Stale downstream: none, no code had been written against the earlier answer | Measured against the live database while planning epic 000 slice 2 | user |
| 2026-09-12 | Added ORM, database driver, migrations and a Python version. Named `gemini-2.5-flash` as the V1 model. Recorded the `SET LOCAL` answer to T-Q2 and that there is no mirrored users table | Decisions AD-2 to AD-7 and AD-9 locked by epic 000's approved build plan, graduated here per rule 6 of the process | user |
| 2026-09-09 | Repository layout moved from `apps/api`, `apps/web`, `packages/` to `backend/` and `frontend/`. Each folder now owns a `rules/repo-rules.md` | User direction | user |

**Downstream documents made stale by the two 2026-09-09 revisions: none.** Rule 7
of the process requires this to be stated rather than assumed. The stack is
consumed at stage 3, and no feature has reached it. Epic 000 is waiting on its
build plan and epic 001 is at stage 2. Neither approved document names a data
layer or a repository path.
