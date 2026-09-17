---
doc: design
feature: 009-notes
title: Notes
stage: 2
status: draft
owner: user
created: 2026-09-17
updated: 2026-09-17
approved_on: null
supersedes: null
---

# Design — Notes

> **Gate skipped.** No approved Epic (stage 0), no approved PRD (stage 1). Drawn
> ahead of both at the user's explicit direction on 2026-09-17, per
> [`CLAUDE.md`](../CLAUDE.md) §2. Nothing here is approved.

Context: PRD not written. Sourced to
[the V1 intake](../product/intake/2026-09-08-personal-jarvis-v1.md) §25.
Canvas: none. Hand-drawn artboards, not Claude Design exports.
Exports: [`./assets/canvas/notes-design.html`](./assets/canvas/notes-design.html)

> **No FR ids exist yet.** Serves cites intake sections. Re-point at real FR
> numbers when the PRD is written.

## 0. What this reuses unchanged

Everything not listed in §2 comes from 001's approved system and is not redrawn
here: the command bar and palette, capture-in-flight, the pending-question
state, the record table, record detail, record edit, delete confirmation, the
shared `EdgeStates`, every colour and type token, the mobile bottom bar and the
dark values. This epic's artboards show only what 001 does not already answer.

## 1. Design intent

Notes is the first record whose body matters more than its title, and that one
fact is the whole design. A note is read, not scanned, so detail drops the field
grid for a measured column at a comfortable line length. The list is cards with
a real excerpt rather than table rows, because a note truncated to a table cell
tells you nothing. And because long text is the first thing in Slashit a user
can lose, every failure state here protects what they typed.

## 2. Screen inventory

| Screen | Purpose | Serves | Artboard |
|---|---|---|---|
| Capture | `/add-note`, title taken from the first line | §25, §36 | `Capture` |
| Reading and editing | Measured reading column; a real text area to edit | §25 | `Reading and editing` |
| List | Cards with excerpts | §25 | `List` |
| States | Five required states, plus unsaved changes | — | `States` |

## 3. Flows

| Flow | Entry | Steps | Exit | Serves |
|---|---|---|---|---|
| Add | Capture | `/add-note …`, title split from body, card confirms | Saved, undoable | §25, §35 |
| Read | Notes | Card, then the reading column | — | §25 |
| Edit | Note detail | Text area, explicit Save | Saved | §25 |

## 4. States

### Note list and editing

| State | What the user sees | Copy |
|---|---|---|
| Empty | Centered serif line and a command to try | "No notes yet" |
| Loading | Four card skeletons in the grid | — |
| Error | Red note | "Notes could not be loaded." |
| Success | Cards, excerpt fading at the card's foot | — |
| **Save failed** | Red note. Says the text survived, first | "Could not save. **Your text is still here** — nothing was cleared. Try again." |
| **Unsaved changes** | Amber note on navigating away | "You have unsaved changes to this note. Leaving now loses them." |
| No permission | Not reachable. Per-account behind sign-in | — |

## 5. Responsive behaviour

| Breakpoint | Layout change |
|---|---|
| Mobile (390px) | Card grid becomes one column. The reading column is already at its comfortable measure and only gains side padding |
| Tablet | Two-column card grid |
| Desktop | Three-column card grid; reading column capped at 660px |

## 6. Design system deltas

| Change | Kind | Token or component | Why existing one does not fit |
|---|---|---|---|
| Reading column | added | component | 660px measure, 1.72 line height. Every other surface is a grid or a table |
| Note card | added | component | Fixed height with an excerpt fading out at the foot |
| Text area | added | component | 001's `.control` is a single 42px line. This is the first multi-line input in the product |
| Character count | added | component | Quiet, right-aligned under the editor |
| Unsaved-changes guard | added | component | **New interaction class: the first place in Slashit where leaving a screen can lose work** |

## 7. Accessibility

| Area | Decision |
|---|---|
| Contrast | Unchanged from 001. The excerpt fade is decorative over `--surface`, and the text beneath it is never the only copy of anything |
| Keyboard path | Cards are links. In the editor, `Tab` moves out of the text area rather than indenting, so the Save button stays reachable |
| Screen reader labels | The unsaved-changes guard is a modal `alertdialog`, focus trapped, "Keep editing" focused by default |
| Motion and reduced motion | None |
| Focus order | On opening the editor, focus lands in the body, not the title. The body is what people came to change |

## 8. Copy

| Location | Text | Notes |
|---|---|---|
| Capture footer | "Slashit took the first line as the title. Change it any time." | Names the inference |
| Save failed | "Could not save. Your text is still here — nothing was cleared. Try again." | Reassurance leads, because losing text is the fear |
| Unsaved changes | "You have unsaved changes to this note. Leaving now loses them." | |
| Guard actions | "Discard" / "Keep editing" | Keep editing is primary. The safe option is the default |
| Editor footer | "Saves when you press Save. Nothing is auto-saved." | Sets the model explicitly, since users assume otherwise |

## 9. Open questions

| # | Question | Owner | Answer |
|---|---|---|---|
| Q1 | Is the body plain text or does it carry formatting? Drawn plain, with paragraph breaks only. Markdown would change the editor, the reading column and the excerpt | user, at epic | Open |
| Q2 | Is there a length limit, and what does exceeding it look like? 001's quota-refusal pattern could be reused | user, at PRD | Open |
| Q3 | Should the editor auto-save as a draft? Drawn as explicit save only, with a guard. Auto-save removes the guard but adds a version question | user, at epic | Open |
| Q4 | `/add-note` splits title from body on the first line. What happens to a one-line note — is the title also the body? | user, at PRD | Open |

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-17 | Created, ahead of the epic and PRD gates | User asked for designs of all upcoming slices, to review later | pending |
