# Slashit

An AI SaaS application. Early stage: the process is set up, the product is
defined, no code is written yet.

## How work happens here

Every feature moves through six gates, and each gate is a document in
`process-docs/`. Nothing gets built without that trail.

```
0 Epic → 1 PRD → 2 Design → 3 Build plan (HLD) → 4 Implementation plan (LLD) → 5 Dev
```

Stage 0 is where the feature is argued out: requirements in detail, pros, cons,
best practices, alternatives. Nothing is locked. Stage 1 locks the requirements.

The user approves each stage before the next one starts. Approval is a user
action in words. Silence is not approval.

**Before writing any document in `process-docs/`, read
[`process-docs/CLAUDE.md`](./process-docs/CLAUDE.md).** It is the binding
ruleset: folder layout, required front matter, what each stage document must
contain, how to write, and change control.

Before drafting any feature document, read
[`process-docs/product/product.md`](./process-docs/product/product.md) for the
standing product context. Before drafting a build plan, also read
[`process-docs/tech-stack.md`](./process-docs/tech-stack.md).

## Rules that bind outside process-docs too

1. **No code before stage 4 is approved.** Sketches inside a doc are fine, files
   in the repo are not. When a big feature splits stage 4 into sub-plans, code
   for a slice waits for the index and that slice's own sub-plan, not for all
   of them.
2. **Do not advance a gate on your own.** If asked to skip ahead, name the
   missing approval first.
3. **Do not invent product facts.** Unknowns go in the doc's Open Questions with
   an owner. Anything you filled in yourself is marked `> Assumption:` in place.
4. **Keep the registry current.** Any stage change updates
   `process-docs/index.md` in the same commit.
5. **Log deviations.** If the build leaves the approved plan, it goes in the
   feature's dev log the day it happens.
6. **Keep technology out of product documents.** Frameworks, vendors and hosting
   choices live in `process-docs/tech-stack.md` and nowhere else. A product
   document or a PRD never names one.
7. **Never commit until asked.** Finish the work, leave it in the working tree,
   and say what changed. The user reads the diff and decides when it becomes a
   commit. This binds even where a rule reads "in the same commit": that says
   what belongs together, not that you may create it. The same applies to
   branching, pushing and opening pull requests.
8. **Every question to the user is multiple choice.** In chat as well as in
   documents. List the defensible options, each with a one-line consequence,
   and put your recommendation first, marked `(Recommended)`. Never leave an
   open question as a bare list of topics for the user to answer in prose.

## Layout

| Path | What it holds |
|---|---|
| `process-docs/` | Product and process documents. Start here. |
| `process-docs/CLAUDE.md` | Rules for writing those documents |
| `process-docs/index.md` | Every feature and its current stage |
| `process-docs/tech-stack.md` | The stack, and why each choice won |
| `process-docs/product/` | What Slashit is, and what V1 ships |
| `process-docs/NNN-<slug>/` | One folder per feature, holding its six stage documents |
