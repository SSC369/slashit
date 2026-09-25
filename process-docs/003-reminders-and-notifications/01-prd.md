---
doc: prd
feature: 003-reminders-and-notifications
title: Reminders and Notifications
stage: 1
status: approved
owner: user
created: 2026-09-23
updated: 2026-09-23
approved_on: 2026-09-23
supersedes: null
---

# Epic PRD — Reminders and Notifications

> **Approved** by @user on 2026-09-23. Locked — changes require a change record (§7).

Context: [Epic](./00-epic.md) · [Product](../product/product.md)

Over the 150-line budget: 40 functional requirements, because time rules
(recurrence, timezones, lateness) each need their own testable line.

## 1. Problem

Slashit records what the user must do, then waits to be asked. Nothing brings
a record back at the moment it matters, so users keep a second app for
reminders, which is the fragmentation Slashit exists to end. The epic argues
this in full: [Problem](./00-epic.md#problem).

## 2. Users and jobs

| User | Job to be done | Today's workaround |
|---|---|---|
| Signed-in user | Be told about something at a set time, once or on a repeat | A phone alarm, a calendar, or a separate reminders app |
| Signed-in user away from Slashit | Still hear about it when the app is closed | Nothing in Slashit reaches them |
| Signed-in user reviewing | See what reminders exist, what fired, and what they missed | None |

## 3. Goals

| # | Goal | What we measure |
|---|---|---|
| G1 | Users set reminders in Slashit | Reminders created per active user per week |
| G2 | Reminders arrive on time | Share of reminders delivered within NFR-1 |
| G3 | Reminders are acted on, not ignored | Share of fired reminders marked done or snoozed within 24 hours |
| G4 | Reminders bring users back | Week-four retention of users with at least one reminder, against those with none |

No numeric targets, following `product.md` §9: with no users there is no
baseline. G2 is the exception, since NFR-1 sets its number.

## 4. Non-goals

- Task alerts. A task's due date does not notify. The notification layer makes
  this cheap later.
- Push, SMS or any channel other than in-app and email. Settled 2026-09-08.
- Calendar recurrence rules: no "last Friday", no end dates, no counts.
- Per-occurrence edits of a recurring reminder.
- Actions from the email itself. The email links into the app, per epic Q4.
- Quiet hours, digests or batching.
- Reminding anyone other than the user.

## 5. User stories

- **US-1.** As a user, I type `/remind` with what and when in one line, so a
  reminder exists without filling a form.
- **US-2.** As a user, I set a reminder that repeats, so routine things come
  back without being set again.
- **US-3.** As a user, I am notified in the app and by email at the set time,
  so I hear about it wherever I am.
- **US-4.** As a user, I mark a fired reminder done, snooze it, or open it, so
  I deal with it from the notification.
- **US-5.** As a user, I see, edit and delete my reminders in Records and with
  `/reminders`, so nothing Slashit will tell me is hidden.
- **US-6.** As a user, I choose my default reminder time and which channels
  reach me, so reminders fit how I live.
- **US-7.** As a user, I see everything Slashit has notified me about in one
  list, so a notification I missed is not lost.

## 6. Functional requirements

| id | Requirement | Priority | Story |
|---|---|---|---|
| FR-1 | `/remind` followed by natural-language text creates a reminder holding a description, a date, a time, and an optional repeat | must | US-1 |
| FR-2 | `/remind` with no date asks one question for when, and creates nothing until answered | must | US-1 |
| FR-3 | `/remind` with a date and no time uses the user's default reminder time | must | US-1, US-6 |
| FR-4 | A time that has already passed today resolves to its next occurrence | must | US-1 |
| FR-5 | The confirmation states the resolved date, time and repeat in words, such as "Tomorrow, 7:00 PM" or "Every Monday, 9:00 AM" | must | US-1 |
| FR-6 | A repeat is daily, weekly on one or more chosen weekdays, monthly on a day of the month, or yearly on a date, each optionally every N | must | US-2 |
| FR-7 | A repeat has no end date and no count | must | US-2 |
| FR-8 | A monthly repeat on a day a month lacks fires on that month's last day. A yearly repeat on February 29 fires on February 28 in other years | must | US-2 |
| FR-9 | A reminder fires at the wall-clock time the user set, in the user's timezone, including across clock changes | must | US-3 |
| FR-10 | After a timezone change, a recurring reminder keeps its wall-clock time in the new zone | must | US-3 |
| FR-11 | After a timezone change, a one-time reminder keeps its original instant | must | US-3 |
| FR-12 | When a reminder fires, a notification enters the user's notification list | must | US-3, US-7 |
| FR-13 | When a reminder fires and the user has the app open, a live notification appears, unless in-app pop-ups are switched off | must | US-3 |
| FR-14 | When a reminder fires, an email goes to the account's email address, unless email is switched off | must | US-3 |
| FR-15 | The email carries the reminder text, its set time, and a link that opens the reminder in Slashit | must | US-3 |
| FR-16 | Each firing produces at most one notification per channel | must | US-3 |
| FR-17 | A reminder that fires up to 24 hours late is delivered on both enabled channels and marked late | must | US-3 |
| FR-18 | A reminder more than 24 hours late enters the notification list marked missed, and sends no email | must | US-3 |
| FR-19 | Marking a fired one-time reminder done closes it | must | US-4 |
| FR-20 | Marking a fired recurring reminder done closes that occurrence; the reminder stays active for its next one | must | US-4 |
| FR-21 | Snooze offers 10 minutes, 1 hour, and tomorrow at the default reminder time, and fires again at the chosen time | must | US-4 |
| FR-22 | Open goes to the reminder's record detail | must | US-4 |
| FR-23 | A fired one-time reminder nobody acted on stays open, listed as fired and not done, until marked done or snoozed | must | US-4 |
| FR-24 | A recurring reminder's next occurrence is scheduled whether or not the previous one was acted on | must | US-2 |
| FR-25 | `/reminders` lists the user's active reminders, soonest next fire first | must | US-5 |
| FR-26 | Records has a Reminders filter, and reminders appear under All | must | US-5 |
| FR-27 | Reminder record detail shows description, next fire time, repeat, origin, creation time, when it last fired, and the action taken then | must | US-5 |
| FR-28 | The user edits a reminder's description, date, time and repeat. An edit to a recurring reminder applies to every future occurrence | must | US-5 |
| FR-29 | Deleting a reminder asks for confirmation. On a recurring reminder it deletes the series | must | US-5 |
| FR-30 | A deleted reminder never fires again | must | US-5 |
| FR-31 | Settings holds a default reminder time, 09:00 until the user changes it | must | US-6 |
| FR-32 | Settings holds a switch for in-app pop-ups and a switch for email, both on by default | must | US-6 |
| FR-33 | The switches never stop a notification entering the notification list | must | US-6, US-7 |
| FR-34 | Turning both switches off shows a one-time warning that nothing will reach the user outside the list | should | US-6 |
| FR-35 | The notification list shows each notification with its text, time, and read or unread state, newest first | must | US-7 |
| FR-36 | The app shows a count of unread notifications wherever the user is | must | US-7 |
| FR-37 | Opening a notification marks it read. The user can mark all read at once | must | US-7 |
| FR-38 | A user holds at most 100 active reminders. Creating a 101st is refused with the reason | must | US-1 |
| FR-39 | A user receives at most 50 reminder emails a day. Past the cap, notifications still enter the list, and the first one past the cap says email is paused until tomorrow | must | US-3 |
| FR-40 | Notifications older than 90 days leave the notification list. Reminder records are unaffected | must | US-7 |

## 7. Non-functional requirements

| id | Requirement | Number | How it is measured |
|---|---|---|---|
| NFR-1 | Firing precision: a notification enters the list after the set time | ≤ 60 s late at p95 | Fire-delay metric, set time against list entry |
| NFR-2 | Email hand-off after firing | ≤ 2 min at p95, `estimate` | Fire time against send-accepted time |
| NFR-3 | Duplicate notifications per firing per channel | 0 | Delivered-count per firing, alert above 1 |
| NFR-4 | Reminders lost, neither fired nor marked missed | 0 | Reconciliation of due reminders against firings |
| NFR-5 | A live notification appears in an open app after firing | ≤ 5 s at p95, `estimate` | Client receipt against list entry |
| NFR-6 | A reminder never fires for, or is visible to, another user | 0 occurrences | Isolation tests, per principle 7 |

## 8. Success metrics

Thirty days after launch.

| Metric | Target | Instrumented by |
|---|---|---|
| Reminders created per active user per week | No target yet, see G1 | Reminder-created events |
| Share delivered within NFR-1 | ≥ 95% | Fire-delay metric |
| Share acted on within 24 hours | No target yet, see G3 | Done and snooze events |
| Week-four retention, with reminders against without | No target yet, see G4 | Retention cohorts |
| Email bounce and spam-complaint rates | No target yet, watched weekly | Email delivery events |

## 9. Dependencies

| Dependency | Type | Owner | Status |
|---|---|---|---|
| Accounts with a verified email and an owner identity | internal | [002](../002-authentication/) | Built, in review |
| Command capture, Records, record detail and Settings with timezone | internal | [001](../001-capture-and-records-foundation/) | Built, in review |
| Interpreting dates, times and repeats from text | internal | [000](../000-ai-gateway/) | Built |
| Work that runs at a set time without a user request | vendor | tech-stack | Resolved, see `tech-stack.md` |
| Outbound email | vendor | tech-stack | Resolved, see `tech-stack.md` |
| Live delivery to an open app | vendor | tech-stack | Resolved, see `tech-stack.md` |

## 10. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A reminder fires late or never, and nobody notices | med | high | NFR-1 and NFR-4 are measured from launch, with an alert |
| Duplicates after a retry or restart | med | med | FR-16, NFR-3 |
| Emails land in spam | med | high | Bounce and complaint rates watched; test to a common free mailbox before launch |
| Repeat phrases misread | med | med | FR-5 echoes the parsed repeat before the user leaves |
| Clock or timezone changes shift a reminder | med | med | FR-9 to FR-11, tested across a real clock change |
| Records and Settings designs, approved in 001, reopen for additions | high | low | Additions only, raised as deltas at design |

## 11. Open questions

| # | Question | Options | Blocks | Owner | Answer |
|---|---|---|---|---|---|
| ~~Q1~~ | Does the reminder email show the reminder text, or only "You have a reminder" with a link? | **(Recommended)** Show the text · Generic text and a link only · A per-user setting | design | user | **Answered 2026-09-23.** Show the text, as FR-15 already states |

## 12. Out of scope

Everything in §4, plus: bulk import or export of reminders, attachments,
location-based reminders, and reminders shared with other users.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-23 | Created from the approved epic. Firing precision (NFR-1), month-end rule (FR-8) and list retention (FR-40) set from the user's answers before drafting | Epic approved | user |
| 2026-09-23 | Q1 answered: the email shows the reminder text. FR-15 unchanged | User chose the recommended option | user |
| 2026-09-23 | Approved | User: "PRD approved, start the design" | user |
