---
doc: epic
feature: 007-events
title: Events
stage: 0
status: approved
owner: user
created: 2026-10-02
updated: 2026-10-03
approved_on: 2026-10-02
supersedes: null
---

# Epic — Events

> **Approved** by @user on 2026-10-02. Locked — changes require a change record (§7).

Context: [Product](../product/product.md) · [V1 features](../product/v1-features.md)

Slightly over the 150-line budget: the user's four answers are recorded verbatim.

## As supplied

The source is [the V1 product definition](../product/intake/2026-09-08-personal-jarvis-v1.md),
§22, with `/add-event` and `/events` in §8.2:

> Events represent things happening at a specific time. `/add-event Mom's birthday October 12`.
>
> V1 capabilities: create, edit, delete, date, time, description, upcoming events.

Opened by the user on 2026-10-02, in parallel with 006, which it does not depend on:

> I am working on expenses in another session parallely, so if 006 is not dependent with it, we can start this in parallel

Answered the same day, as chosen from the options offered:

| Question | Answer |
|---|---|
| Should events repeat? | "Yearly only" |
| How do events connect to reminders? | "Optional lead-time alert" |
| What time shape does an event have? | "Date, optional time, optional end" |
| External calendar sync in 007? | "No, defer past V1" |

## Problem

J3, "What is happening?", has no answer in Slashit today. Birthdays, appointments
and trips live in a calendar app, so the user still keeps two places, which is
the fragmentation `product.md` §2 names.

The nearest substitutes are wrong shapes. A task with a due date is something to
finish; Mom's birthday is not finished. A reminder is a notification at an
instant; a dinner from 7 to 9 PM is a span of time the user wants to see ahead.

Daily Control (010) also cannot show "1 Event" in Today or "Birthday" in Upcoming
until events exist as records.

## What this feature is

A new record type, the event, captured with `/add-event Mom's birthday October 12`
and listed soonest first with `/events`. An event has a title, a date, an optional
start time, an optional end, an optional location, and an optional description. With no time it is
all-day. It can repeat yearly, for birthdays and anniversaries. The capture line
can ask for alerts, as in "remind me 1 week and 1 day before", each of which sets
a reminder tied to the event through 003's notification layer. Like every record, it appears in
Records with its own filter and can be edited and deleted.

## Requirements in detail

| Area | What it has to do | Why it matters | Notes |
|---|---|---|---|
| Capture | `/add-event` pulls a title, date, optional time, optional end, optional location, optional yearly repeat and any number of alerts out of one line | P1: one line in, a record out | Same interpretation path as 001's task due dates and 003's `/remind` |
| No date | Ask one question, per the confirmation model | An event without a date is a note | "Dentist" alone is ambiguous; "dentist Friday 4pm" is not |
| Past date | "October 12" said on October 20 needs a rule | Silently filing it in the past hides it from `/events` | The next occurrence, echoed in the confirmation, per Q1 |
| All-day vs timed | No time means all-day; a time makes it timed | Birthdays have no time, appointments do | All-day events belong to a local date, not an instant. They must not drift a day after a timezone change |
| End | Optional end time ("3 to 5 PM") or end date ("Oct 12 to Oct 15") | Trips and blocks of time | An end before the start means the next day, echoed back, per Q2 |
| Location | An optional place, as in "at Apollo Hospital" | Where to be, searchable on its own | Added per Q6, beyond the source. Free text, no maps or place lookup |
| Yearly repeat | "every year", or a birthday or anniversary phrase, repeats on the same date | The main recurring event the source names | Feb 29 follows 003's FR-8 rule: Feb 28 in other years. Edits apply to the series, as in 003 |
| Alerts | "remind me 1 day before" creates a reminder that fires that long before the event. An event carries any number of alerts, each with its own lead | Seeing an event ahead is not enough for a birthday gift; a gift needs a week, the call needs the morning | Reuses 003's delivery, channels and caps. No cap per event, per Q5 as reversed. Moving the event moves every alert; deleting it deletes them all, per Q3 |
| `/events` | Lists upcoming events, soonest first, a yearly event at its next occurrence | The source's "upcoming events" | Past events leave this list and stay in Records marked past, per Q4 |
| Records | An Events filter, events under All, and record detail with every field, next occurrence, alert, origin and creation time | "If Slashit can record it, the user can see it" | Grows 001's approved Records design |
| Edit and delete | Change any field; delete with confirmation, soft-deleted per `product.md` §4 | P4 | Deleting a yearly event deletes the series |
| Search | Events are found by 005's personal search and used in its answers | P3, and "when is Mom's birthday?" is a likely question | A new record type joins 005's index; 005 is not a dependency, but 007 must plug into it once both exist |
| Limits | A cap on active events per user | Same abuse argument as 003's FR-38 | > Assumption: 500 active events, `estimate`. Events accumulate faster than reminders because they are not closed |
| Metrics | Events created, with time or all-day, with end, yearly, with alert; edits within five minutes | Shows which parts of the shape earn their place | Per `product.md` §9 |

## Pros

- Answers J3 and removes the second app for dates, serving the one-place promise.
- Serves P3: "Mom's birthday" told once comes back every year, with an alert.
- Small and well understood. `v1-features.md` §6 calls it near-identical in shape
  to 006 and 009, layered on 001's working loop.
- Reuses 003's reminder and notification layer rather than building delivery again.
- Unblocks 010, whose Today and Upcoming views need events.

## Cons

- A third time-bearing record type beside tasks and reminders. Users may not know
  whether "dentist Friday 4pm" is an event or a reminder, and commands-only
  capture makes them choose.
- All-day events are a new time kind. Every earlier date in Slashit is an instant
  or a due date; a local date that must not shift with timezone is a new rule.
- Any number of alerts per event, with no cap of its own, lets one event spend
  much of 003's 100 active reminders. The shared cap still bounds the total.
- Tying a reminder to an event couples 007 to 003. Moving or deleting the event
  must keep the alert consistent, which is a cross-type rule nothing has had yet.
- Yearly repeat duplicates part of 003's recurrence. Sharing the logic is cheaper
  long term; copying it is cheaper now.
- Reopens 001's approved Records design for a new filter and a new detail layout.
- Without calendar sync, users who already live in a calendar app may keep it,
  and Slashit becomes a second copy rather than the one place.

## Best practices and prior art

| Product | How they do it | What to take | What to avoid |
|---|---|---|---|
| Google Calendar | All-day and timed events, optional end, recurrence, per-event notifications such as "1 day before" | The all-day versus timed split, and alerts expressed as a lead time | Full recurrence rules and "this event, following, all" edit prompts |
| Fantastical | Natural-language entry: "Lunch with Sam Friday 1pm to 2pm, alert 30 minutes before" parsed in one line, echoed back before saving | One line carrying time, end and alert; show the parsed result | Its parser guesses silently on ambiguous phrases. Ask one question instead |
| Apple Calendar | Birthdays come from contacts and repeat yearly; all-day events show at the top of the day | Yearly birthdays as the headline recurring case | Contacts integration, a third-party dependency |
| Todoist | No events; due dates on tasks stand in for them | Evidence that tasks are a poor fit: users complain birthdays show as overdue | Modelling events as tasks |

## Alternatives considered

| Option | What it gives | What it costs | Verdict |
|---|---|---|---|
| Do nothing | No new type | J3 unanswered; 010 has no events to show | Rejected. In the source at P1 |
| Events as tasks with a due date | No new type | Birthdays turn overdue and need completing; no all-day or end | Rejected |
| Events as reminders | Reuses 003 wholesale | A reminder is an instant to notify, not a span to see ahead | Rejected |
| Full recurrence, as in 003 | Weekly classes, monthly bills as events | Overlaps reminders, more parsing and tests | Rejected by the user, 2026-10-02 |
| No reminder link | Smallest 007 | User runs `/remind` separately and must keep both in step | Rejected by the user, 2026-10-02 |
| External calendar sync or export | Events where the user already looks | Third-party integration, a V1 non-goal | Deferred by the user, 2026-10-02 |

## Risks and unknowns

| Risk | Likelihood | Impact | What would tell us early |
|---|---|---|---|
| Users confuse `/add-event` and `/remind` | medium | medium | Events created then deleted and re-added as reminders, or the reverse |
| All-day events shift a day after a timezone change | medium | high | A test that changes timezone across the date line |
| Alert and event fall out of step after an edit or delete | medium | medium | Reminders whose event is deleted or moved, counted nightly |
| Ranges and lead times are misread ("Friday to Sunday", "a week before") | medium | medium | Edits within five minutes of capture |
| Records list grows with past events and buries upcoming ones | low | low | Share of Records views filtered to Events |

## Open questions

All six answered by the user on 2026-10-02. Q1 to Q5 as recommended; Q6 chose the field over the description.

| # | Question | Answer | Blocks | Owner |
|---|---|---|---|---|
| ~~Q1~~ | A date already passed this year, with no year given? | **Next occurrence, echoed in the confirmation**, as 003's Q8 | PRD | user |
| ~~Q2~~ | End before start, as in "11 PM to 1 AM"? | **Ends the next day, echoed back** | PRD | user |
| ~~Q3~~ | What happens to the alert when its event changes? | **Moves with the event; deleted with it** | PRD, build plan | user |
| ~~Q4~~ | Where do past events go? | **Leave `/events`, stay in Records with a past marker** | PRD | user |
| ~~Q5~~ | Can one event carry more than one alert? | **One alert in V1.** Reversed by the user on 2026-10-02, during slice 1's build: **any number of alerts, no cap per event** (dev log X-1) | PRD | user |
| ~~Q6~~ | Location field? Not in the source | **Optional location field**, not the recommended option | PRD | user |

## What this is not

- Not calendar sync, import, export or subscription.
- Not recurrence beyond yearly: no weekly, monthly or custom rules, no per-occurrence edits.
- Not invitations, attendees, or events shared with other people.
- Not time zones per event. An event lives in the user's timezone.
- Not a calendar grid view. Today and Upcoming are 010's.
- Not contacts integration for birthdays.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-10-02 | Created, with the user's four scoping answers recorded | User asked to start 007 in parallel with 006 | user |
| 2026-10-02 | Q1 to Q6 answered and closed; requirement notes updated; optional location added | User answered all six | user |
| 2026-10-02 | Approved | User: "Approve, write the PRD" | user |
| 2026-10-03 | Q5 reversed: any number of alerts per event, no cap per event. What this feature is, the Alerts row and Cons updated. Stale: PRD, design, build plan, implementation plan index and 4.1, in that order. Slice 1's built "which alert?" question becomes a deviation once the PRD change is approved | User decided X-1 on 2026-10-02: "allow any number of alerts". Change approved 2026-10-03 | user |
