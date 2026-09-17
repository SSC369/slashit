---
doc: design
feature: 005-personal-search-and-context
title: Personal Search and Context
stage: 2
status: draft
owner: user
created: 2026-09-17
updated: 2026-09-17
approved_on: null
supersedes: null
---

# Design — Personal Search and Context

> **Gate skipped.** No approved Epic (stage 0), no approved PRD (stage 1). Drawn
> ahead of both at the user's explicit direction on 2026-09-17, per
> [`CLAUDE.md`](../CLAUDE.md) §2. Nothing here is approved.

Context: PRD not written. Sourced to
[the V1 intake](../product/intake/2026-09-08-personal-jarvis-v1.md) §27, §28.
Canvas: none. Hand-drawn artboards, not Claude Design exports.
Exports: [`./assets/canvas/search-design.html`](./assets/canvas/search-design.html)

> **No FR ids exist yet.** Serves cites intake sections. Re-point when the PRD
> is written.

## 1. Design intent

The intake's requirement is one sentence and it decides the whole design: the
user should not need to know which category holds the information. So results
are one list, not tabs you must choose between first, and the type is a quiet
label rather than a grouping. The second half, relationships, follows the same
honesty rule as memory: every link Slashit worked out itself is labelled as
inferred and can be removed, because a connection you cannot see or correct is
a connection you cannot trust.

## 2. Screen inventory

| Screen | Purpose | Serves | Artboard |
|---|---|---|---|
| Results | One ranked list across every record type | §27 | `Results` |
| Relationships | What connects to what, and who said so | §28 | `Relationships` |
| Related in detail | The same links folded into 001's record detail | §28 | `RelatedInDetail` |
| States | Five required states, plus no-match and partial failure | — | `States` |
| Mobile | 390 × 844 | §27, §28 | `Mobile` |

## 3. Flows

| Flow | Entry | Steps | Exit | Serves |
|---|---|---|---|---|
| Search | Capture or the search field | `/search <term>`, one list, optional type filter | Record detail | §27 |
| Narrow | Results | Click a type tab, list filters in place, query unchanged | — | §27 |
| Explore a link | Record detail, Related | Click a related record | That record's detail | §28 |
| Correct a link | Relationships | Remove an inferred link | Link gone, records intact | §28 |

## 4. States

### Results

| State | What the user sees | Copy |
|---|---|---|
| Empty, before a query | Suggested recent terms as chips | "Search everything at once" / "Tasks, reminders, memories, notes and goals, in one place." |
| Loading | Three row skeletons at result height | — |
| Error | Red note. Separates the failure from the data | "Search is unavailable. Your records are fine — only searching them is down." |
| Success | Rows, type label left, match highlighted | — |
| **No match** | Centered, serif, **not error styling** | "Nothing matched `quarterly`" / "Slashit searched every record type. Nothing here uses that word yet." |
| Partial failure | Amber note above real results, naming what is missing | "Memories could not be searched this time. Everything below excludes them." |
| No permission | Search only ever spans the signed-in account's own records, so there is no cross-account denial to render | — |

### Relationships

| State | What the user sees | Copy |
|---|---|---|
| Empty | No tree, one line under the record | "Nothing connects to this yet." |
| Loading | Skeleton nodes at tree indents | — |
| Error | Amber note. The record itself still renders | "Related records could not be loaded." |
| Success | Tree, goal node on blue wash, why-label per edge | — |
| No permission | N/A, same reason as above | — |

## 5. Responsive behaviour

| Breakpoint | Layout change |
|---|---|
| Mobile (390px) | Search moves into the header as the full-width field. Type filters become horizontally scrolling chips. The tree halves its indent and drops why-labels to a second line |
| Tablet | No distinct layout |
| Desktop | Type filters as tabs in the topbar with counts; results max 760px |

## 6. Design system deltas

| Change | Kind | Token or component | Why existing one does not fit |
|---|---|---|---|
| Result row | added | component | Type label, title, and the matched line. A record row assumes one type per table |
| Match highlight | added | token | Amber-tinted background behind matched text. New: 001 has no highlight token, and the existing washes are semantic (status), which this is not |
| Relationship tree | added | component | **The first nested structure in the product.** Everything before it is a flat list or a table |
| Why-label | added | component | "you linked this" / "Slashit inferred this" on each edge |
| Related list | added | component | Compact rows inside record detail, distinct from the tree |
| Type filter tabs with counts | changed | `.tabs` | 001's tabs carry no count |

## 6a. Dark theme

Added 2026-09-17, alongside the rest of this design. Dark reuses **001's
approved palette unchanged** — the eighteen token pairs in its `DarkTokens`
artboard, which the shipped `frontend/src/design-system/tokens.css` already
carries byte-for-byte. **This epic adds no colour token**, and it inherits
001's one dark-specific rule: a primary button inverts to a light blue field
with dark ink on it, never white.

Dark artboards on the canvas: `Results`, `Relationships`. States and mobile panels are not
redrawn in dark — they are the same components on the same tokens, and 001
took the same representative-subset approach rather than doubling its canvas.

### Defect found by drawing dark

**The match highlight was broken.** `.hl` was a hardcoded light tint that set
no text colour, so on dark it rendered near-white text on pale yellow and the
matched word disappeared — the exact thing the highlight exists to do. Q4
already flagged the tint as unmeasured for contrast; dark is what turned that
into a defect rather than a question. Fixed to a dark amber field with light
amber text. **Q4 stays open for the light theme**, which is still unmeasured.

## 7. Accessibility

| Area | Decision |
|---|---|
| Contrast | The match highlight needs checking against `--ink` at the amber tint drawn; it is the one new colour here and it has not been measured. Flagged as Q4 |
| Keyboard path | Results are a list; arrow keys move between rows, Enter opens. Type tabs are a tab list. The tree is a `treeview`: arrows move and collapse |
| Screen reader labels | Each result announces its type first ("Memory, Passport expires in 2030"), because type is the disambiguator. Tree nodes announce depth and relationship, and why-labels are read, not decorative |
| Motion and reduced motion | None. No animation in this epic |
| Focus order | After a search, focus moves to the first result, not back to the field |

## 8. Copy

| Location | Text | Notes |
|---|---|---|
| Empty | "Search everything at once" | States the promise from §27 directly |
| No match | "Nothing matched `quarterly`" | Quotes the term. Never "no results found" |
| No match, second line | "Slashit searched every record type. Nothing here uses that word yet." | Confirms the search was complete, so the user does not re-search elsewhere |
| Error | "Search is unavailable. Your records are fine — only searching them is down." | Separates index failure from data loss |
| Inferred link | "Slashit inferred this" | Versus "you linked this". Always one or the other, never blank |
| Inference note | "Links Slashit worked out itself are labelled Slashit inferred this. Every one can be removed, and removing it does not delete the record." | |

## 9. Open questions

| # | Question | Owner | Answer |
|---|---|---|---|
| Q1 | Is search literal, semantic, or both? The drawn highlight assumes a literal match exists to highlight; a semantic result may have none | user, at epic | Open |
| Q2 | Does `/search <question>` route to 004's prose answer and `/search <term>` to this list, or is there one surface? They overlap by design and this is the seam | user, at epic | Open |
| Q3 | Who creates relationships — the model at capture, a background pass, or the user only? Drawn as both inferred and manual | user, at epic | Open |
| Q4 | The match-highlight tint is new and unmeasured for contrast **in light**. The dark value was fixed on sight (§6a) because dark made it a visible defect; the light one is still only assumed to pass | user, at design review | Open |
| Q5 | Ranking across types. A task and a memory both matching — which leads? Drawn ungrouped, which makes ranking visible and therefore arguable | user, at build plan | Open |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-17 | Created, ahead of the epic and PRD gates | User asked for designs of all upcoming slices, to review later | pending |
| 2026-09-17 | Dark theme added (§6a), reusing 001's approved palette unchanged | User asked for dark designs alongside the light ones | pending |
