---
doc: prd
feature: 007-events
title: Events
stage: 1
status: approved
owner: user
created: 2026-10-02
updated: 2026-10-02
approved_on: 2026-10-02
supersedes: null
---

# Epic PRD — Events

> **Approved** by @user on 2026-10-02. Locked — changes require a change record (§7).

Context: [Epic](./00-epic.md) · [Product](../product/product.md)

Over the 150-line budget at about 160: 33 functional requirements, because time
rules and the alert's coupling to its event each need their own testable line.

## 1. Problem

Slashit cannot answer J3, "What is happening?". Birthdays, appointments and trips
stay in a calendar app, and neither a task nor a reminder has the right shape for
them. Daily Control (010) has no events to show until this exists. The epic argues
this in full: [Problem](./00-epic.md#problem).

## 2. Users and jobs

| User | Job to be done | Today's workaround |
|---|---|---|
| Signed-in user | Record something happening on a date, with a time and place when there is one | A calendar app |
| Signed-in user | Be told ahead of an event, such as a birthday a day early | A calendar alert, or a separate `/remind` they keep in step by hand |
| Signed-in user | See what is coming up, and look back at what has happened | A calendar app |

## 3. Goals

| # | Goal | What we measure |
|---|---|---|
| G1 | Users record events in Slashit | Events created per active user per week |
| G2 | Capture is trusted | Share of events edited within five minutes of creation |
| G3 | Alerts earn their place | Share of events created with an alert |

No numeric targets, following `product.md` §9: with no users there is no baseline.

## 4. Non-goals

- Calendar sync, import, export or subscription. Deferred by the user, 2026-10-02.
- Recurrence other than yearly, and per-occurrence edits.
- More than one alert per event, per epic Q5.
- Invitations, attendees, or events shared with anyone.
- A timezone per event. Every event lives in the user's timezone.
- A calendar grid, and Today and Upcoming views. Those are 010's.
- Place lookup or maps. A location is free text.

## 5. User stories

- **US-1.** As a user, I type `/add-event` with what and when in one line, so an event exists without a form.
- **US-2.** As a user, I record birthdays and anniversaries once, so they come back every year.
- **US-3.** As a user, I ask for an alert in the same line, so I hear about an event before it starts.
- **US-4.** As a user, I list what is coming up with `/events`, so I know what is happening.
- **US-5.** As a user, I see, edit and delete my events in Records, so nothing recorded is hidden.

## 6. Functional requirements

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-1 | `/add-event` followed by text creates an event holding a title, a date, and optionally a start time, an end, a location, a description, a yearly repeat and one alert. It appears in command discovery under `/add` (001 FR-2) | must | US-1 |
| FR-2 | `/add-event` with no date asks one question for when, and creates nothing until answered | must | US-1 |
| FR-3 | An event with no start time is all-day | must | US-1 |
| FR-4 | A date with no year that has already passed this year resolves to next year | must | US-1 |
| FR-5 | A date with an explicit past year is saved as given and shown as past | must | US-1, US-5 |
| FR-6 | An end is a time on the same day, or a later date for a multi-day event | must | US-1 |
| FR-7 | An end time earlier than the start time means the next day | must | US-1 |
| FR-8 | The confirmation states the resolved date, time, end, location, repeat and alert in words, such as "Sat 12 Oct, all day, every year, alert 1 day before" | must | US-1 |
| FR-9 | "every year", or a title naming a birthday or anniversary, makes the event repeat yearly on the same date | must | US-2 |
| FR-10 | A yearly event on February 29 occurs on February 28 in other years, as 003's FR-8 | must | US-2 |
| FR-11 | An edit to a yearly event applies to every occurrence. Deleting it deletes the series | must | US-2, US-5 |
| FR-12 | An all-day event stays on its date after the user's timezone changes | must | US-1 |
| FR-13 | After a timezone change, a one-time timed event keeps its original instant, per 001 FR-28. A yearly timed event keeps its wall-clock time in the new zone, as 003's FR-10 | must | US-1, US-2 |
| FR-14 | "remind me <lead> before", or similar, sets one alert that fires that long before the event starts | must | US-3 |
| FR-15 | On an all-day event the alert counts back from the user's default reminder time on the event's date (003 FR-31). "1 day before" fires the day before at that time | must | US-3 |
| FR-16 | A capture naming more than one alert asks which one to keep | must | US-3 |
| FR-17 | An alert is delivered as a reminder notification: same channels, switches and caps as 003 (FR-12 to FR-14, FR-32, FR-38, FR-39) | must | US-3 |
| FR-18 | The alert's notification names the event and its start, and opens the event's record detail | must | US-3 |
| FR-19 | An alert whose fire time has already passed at capture or edit is not set, and the confirmation says so | must | US-3 |
| FR-20 | On a yearly event the alert fires before every occurrence | must | US-2, US-3 |
| FR-21 | Changing an event's date or start time moves its alert by the same lead | must | US-3, US-5 |
| FR-22 | The user adds, changes or removes an event's alert by editing the event | must | US-3, US-5 |
| FR-23 | Deleting an event deletes its alert. A pending alert never fires for a deleted event | must | US-3, US-5 |
| FR-24 | `/events` lists upcoming events soonest first: yearly events at their next occurrence, and multi-day events until their end | must | US-4 |
| FR-25 | A one-time event leaves `/events` once its end has passed, or once its date has passed when it has no end. It stays in Records, marked past | must | US-4, US-5 |
| FR-26 | Records has an Events filter, and events appear under All | must | US-5 |
| FR-27 | Event record detail shows every field, the next occurrence, the alert and when it fires, origin and creation time | must | US-5 |
| FR-28 | The user edits every field of an event | must | US-5 |
| FR-29 | Deleting an event asks for confirmation and soft-deletes it, per `product.md` §4 | must | US-5 |
| FR-30 | Events are found by personal search and can support its answers, as every other record type (005) | must | US-4 |
| FR-31 | A user holds at most 500 upcoming events. Creating the 501st is refused with the reason | must | US-1 |
| FR-32 | An event's alert appears only on the event. It is not listed by `/reminders` or under the Reminders filter | must | US-3, US-5 |
| FR-33 | An event's alert counts toward the 100 active reminders of 003's FR-38. An alert past that cap is not set, and the confirmation says so; the event is still created | must | US-3 |

> Assumption: FR-9's birthday and anniversary rule follows epic §Requirements; the echo in FR-8 is the guard against a wrong guess.
>
> Assumption: FR-5 and FR-19 are not argued in the epic. They fill gaps its Q1 and Q3 leave: a past year given on purpose, and a lead that has already passed.
>
> Assumption: FR-31's 500 is an `estimate`, carried from the epic. Past events do not count.

## 7. Non-functional requirements

| id | Requirement | Number | How it is measured |
|---|---|---|---|
| NFR-1 | Capture acknowledgement, as 001 NFR-2 | Under 1.5 s at p95 | Server timing, submit to first byte |
| NFR-2 | Field extraction correct on everyday event input, including ranges, yearly phrases and alert leads | Over 90% of fields correct, as 001 NFR-4 | Labelled evaluation set, built before build plan approval |
| NFR-3 | All-day events shown on a different date than recorded | 0 | Tests across timezone changes, including across the date line |
| NFR-4 | Alerts out of step with their event: firing after the event moved, or for a deleted event | 0 | Nightly reconciliation of alerts against events |
| NFR-5 | Alert firing precision, as 003 NFR-1 | ≤ 60 s late at p95 | 003's fire-delay metric |
| NFR-6 | An event or its alert is never visible to, or fired for, another user | 0 occurrences | Isolation tests, per principle 7 |

## 8. Success metrics

Thirty days after launch.

| Metric | Target | Instrumented by |
|---|---|---|
| Events created per active user per week | No target yet, see G1 | Event-created events |
| Share edited within five minutes | No target yet, see G2 | Edit events against creation time |
| Share with an alert, all-day, with end, with location, yearly | No target yet, see G3 | Event-created events, by field |
| Events deleted then re-added as reminders within a day | No target yet, watched | Delete and create events |

## 9. Dependencies

| Dependency | Type | Owner | Status |
|---|---|---|---|
| Accounts and an owner identity | internal | [002](../002-authentication/) | Built, in review |
| Command capture, Records, record detail, Settings with timezone | internal | [001](../001-capture-and-records-foundation/) | Built, in review |
| Interpreting dates, times, ranges and leads from text | internal | [000](../000-ai-gateway/) | Built |
| Reminder delivery, default reminder time, channel switches and caps | internal | [003](../003-reminders-and-notifications/) | Shipped |
| Personal search over every record type | internal | [005](../005-personal-search-and-context/) | Built, in progress. Needed for FR-30 only |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Users confuse `/add-event` and `/remind` | med | med | Last metric in §8 shows it; command discovery describes each |
| All-day events shift a day after a timezone change | med | high | FR-12, NFR-3 |
| Alert and event fall out of step | med | med | FR-21 to FR-23, NFR-4 |
| A title is wrongly read as a birthday and repeats | med | low | FR-8 echoes the repeat; one edit removes it |
| Records, record detail and command discovery, approved in 001, reopen for additions | high | low | Additions only, raised as deltas at design |

## 11. Open questions

| # | Question | Options | Blocks | Owner | Answer |
|---|---|---|---|---|---|
| ~~Q1~~ | Does an event's alert also appear as its own reminder in `/reminders` and the Reminders filter? | **(Recommended)** No, it shows only on the event, so one thing has one record · Yes, as a linked reminder the user can open | design, hld | user | **Answered 2026-10-02.** Only on the event. FR-32 added |
| ~~Q2~~ | Does an alert count against 003's 100 active reminders cap (FR-38)? | **(Recommended)** Yes, one shared cap, simplest to explain · No, events' alerts are capped only by FR-31 | hld | user | **Answered 2026-10-02.** One shared cap. FR-33 added |

## 12. Out of scope

Everything in §4, plus: bulk import or export of events, attachments, colour or
category labels, and travel time.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-10-02 | Created from the approved epic | Epic approved | user |
| 2026-10-02 | Q1 and Q2 answered; FR-32 and FR-33 added | User chose the recommended options | user |
| 2026-10-02 | Approved | User: "Approve, start design" | user |
