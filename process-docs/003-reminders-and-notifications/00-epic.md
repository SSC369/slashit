---
doc: epic
feature: 003-reminders-and-notifications
title: Reminders and Notifications
stage: 0
status: approved
owner: user
created: 2026-09-23
updated: 2026-09-23
approved_on: 2026-09-23
supersedes: null
---

# Epic — Reminders and Notifications

> **Approved** by @user on 2026-09-23. Locked — changes require a change record (§7).

Context: [Product](../product/product.md) · [V1 features](../product/v1-features.md)

Over the 150-line budget at about 190: the source settled three decisions and the
user fourteen more, and recording them verbatim costs about 40 lines.

## As supplied

The source is [the V1 product definition](../product/intake/2026-09-08-personal-jarvis-v1.md),
§21 (Reminders), with `/remind` and `/reminders` in §8.2. Decisions already
carried here from [001's PRD](../001-capture-and-records-foundation/01-prd.md#open-questions):

| Settled | Answer | Where |
|---|---|---|
| How a reminder reaches the user | In-app and email. No push. Both ship, the user can disable either | 001 PRD Q2, 2026-09-08 |
| Recurring reminders | In V1, with the scheduling they need | 001 PRD Q13, 2026-09-08 |
| Default reminder time | Belongs to this epic, not 001's settings | 001 PRD Q8, 2026-09-08 |

Opened by the user on 2026-09-23:

> For now proceed with 003 feature

Answered the same day, as chosen from the options offered:

| Question | Answer |
|---|---|
| What is a reminder, relative to a task with a due date? | "Own type, tasks later" |
| How rich is recurrence? | "Presets + interval" |
| What can the user do when a reminder fires? | "Mark done, Snooze, Open the record" |
| Date given, no time? | "Default time in Settings" |

## Problem

Slashit records what the user needs to do and then waits to be asked. A task
due tomorrow sits in Records until the user happens to open it. J1, "What do I
need to do?", is answered only for a user who remembers to look, which is the
user who needed Slashit least.

Every reminder the user sets today lives in a second app. That is the
fragmentation `product.md` §2 names as the problem, and it keeps Slashit from
being the one place.

This is also the first feature in which Slashit acts while the user is away.
Until now, every failure was visible the moment it happened. A reminder that
fails to fire is invisible until the thing it was for has already been missed.

## What this feature is

A new record type, the reminder, captured with `/remind Call Mom tomorrow at 7pm`
and listed with `/reminders`. At the set time Slashit notifies the user in the
app and by email. From the notification the user marks it done, snoozes it, or
opens it. A reminder can repeat: daily, on chosen weekdays, monthly or yearly,
each optionally every N. Like every record, it appears in Records and can be
edited and deleted.

Underneath sits a notification layer that later epics reuse: a per-user list of
what Slashit has told them, and two delivery channels. Tasks do not notify in
this epic. Events (007), Daily Control (010) and Proactive Slashit (011) are
the expected next callers.

## Requirements in detail

| Area | What it has to do | Why it matters | Notes |
|---|---|---|---|
| Capture | `/remind` pulls a description, a date, an optional time and an optional repeat out of one line | P1: one line in, a record out | Same interpretation path as 001's task due dates. Repeat phrases ("every other Monday") are new and harder than dates |
| No date | Ask one question, per the confirmation model | A reminder with no time is a note | "Remind me to call Mom" is ambiguous; "tomorrow" is not |
| Date, no time | Fire at the user's default reminder time, shown in the confirmation | No friction for the common case | The default starts at 09:00 local, changeable in Settings. > Assumption: 09:00, following Google Tasks |
| Time already passed | "7pm" said at 8pm needs a rule | Silently scheduling in the past loses the reminder | The next 7pm, echoed in the confirmation, per Q8 |
| Recurrence | Daily, weekly on chosen weekdays, monthly, yearly, and every N of each. No end date, no count | Covers "every Monday", "every 2 weeks", "every Oct 12" | Monthly on the 31st and yearly on Feb 29 need a stated rule |
| Local time | A reminder fires at the wall-clock time the user said, in their timezone | "7pm" means 7pm, including after a clock change | Timezone lives in 001's Settings. A change moves recurring reminders to the new zone and leaves one-time ones alone, per Q2 |
| Firing | Deliver close to the set time, every time | The whole feature is this row | The PRD sets the number. Up to 24 hours late delivers marked late; past that, missed in-app only, per Q3 |
| Exactly once | One reminder, one notification per channel, even across retries and restarts | A duplicate is noise; three duplicates is spam | This is the part that looks simple and is not |
| In-app delivery | A notification appears live when the app is open, and waits in a notification list when it is not | The user must be able to see what Slashit told them (P2) | Read and unread state. The list always records, whatever the switches say, per Q7. It is the reusable part |
| Email delivery | Sent to the account's verified email | Reaches a user who is not in the app | Deliverability, bounces and spam placement are real risks |
| Channel control | Either channel can be switched off in Settings | Settled in 001 PRD Q2 | Switches cover the live pop-up and email, never the list. Warn once when both are off, per Q7 |
| Mark done | Closes a one-time reminder. A recurring one moves to its next occurrence | The user acts on it and it goes away | Until then a fired one-time reminder stays open, per Q10 |
| Snooze | Fires again after a fixed choice | "Not now" without losing it | 10 minutes, 1 hour, tomorrow at the default time, per Q5 |
| Open | Goes to the reminder's record detail | Edit or delete from where the user already is | The email links here; no action works from the email itself, per Q4 |
| Records | A Reminders filter, a list, and record detail with next fire time, repeat and origin | "If Slashit can record it, the user can see it" | Source §11's Records list omits reminders; added per Q1. Detail shows last fired and its outcome, per Q6 |
| Edit and delete | Change text, time or repeat; delete with confirmation | P4 | A recurring edit changes the series. > Assumption: no per-occurrence edits in V1 |
| Limits | A cap on active reminders and emails per user per day | Email costs money and can be abused | 100 active, 50 emails a day, `estimate`, per Q9 |
| Metrics | Reminders created, fired, delivered per channel, marked done, snoozed, fire delay | H1 and H3, and the only way to know firing works | Instrumented from launch, per `product.md` §9 |

## Pros

- Completes J1. Tasks say what to do, and reminders say when.
- Serves P3. Slashit uses what it was told, unprompted, at the right time.
- A reason to come back that the user did not have to remember. It is the most
  direct lever on H3's week-four retention.
- Builds the notification layer once. Events, Daily Control and Proactive
  Slashit reuse it instead of each building delivery.
- Recurrence built here can serve task recurrence later, which
  [V1 features](../product/v1-features.md#8-later-versions) names as the trigger for that.

## Cons

- The first time-critical feature. A missed reminder costs more trust than no
  reminder feature, because the user stopped keeping their own.
- Adds always-on background work. Every earlier feature ran only when a user
  made a request. This one needs something running at 3am to fire a reminder
  set for then, and that has to be watched.
- Email is outbound and costs per send. It can land in spam, bounce, or be
  marked as spam, and repeated complaints damage delivery for every user.
- Time is where bugs hide: clock changes, timezone changes, month ends, leap
  days, and "7pm" said at 8pm. Each needs a rule and a test.
- Hard to verify by hand. A daily reminder takes a day to prove it repeats.
- Grows Records and Settings, both already designed and approved in 001, so
  their designs reopen for additions.

## Best practices and prior art

| Product | How they do it | What to take | What to avoid |
|---|---|---|---|
| Slack `/remind` | One command, natural-language time and repeat ("every Tuesday at 3pm"). The reminder arrives as a message with mark-complete and snooze choices | The closest analogue: command-first, repeat in the same line, actions on the notification | Its repeat grammar surprises users on edge phrases. Show the parsed schedule back every time |
| Todoist | Natural-language dates and repeats on tasks ("every other Monday"); reminders are alerts attached to tasks | Echo the parsed recurrence in plain words before trusting it | Merging reminders into tasks. The user chose a separate type for now |
| Apple Reminders | Reminders are their own list. Date-only reminders notify at a time set once in Settings. Repeat presets plus a custom rule | The default-time setting, which the user has chosen here | Its custom-repeat builder, a form, which P1 rules out as primary input |
| Google Tasks | Date-only tasks notify at 09:00 by default | A sensible default so no question is asked | |
| Google Calendar | Full calendar recurrence rules, per-occurrence edits, "this, this and following, all" on edit | Proof of how much cost full rules carry | Per-occurrence edits in V1. The three-way edit prompt confuses users |

## Alternatives considered

| Option | What it gives | What it costs | Verdict |
|---|---|---|---|
| Do nothing | No new moving parts | J1 half answered; users keep a second app | Rejected. P0 in the source |
| Alerts on tasks, no reminder type | One fewer record type | Drops `/remind`, goes against the source, changes 001's tasks | Rejected by the user, 2026-09-23 |
| Reminders plus task due alerts | Tasks notify from day one | A bigger epic, and it reopens 001 | Deferred. The notification layer makes it cheap later |
| In-app only | No email cost or deliverability risk | Useless when the app is closed, which is when a reminder matters | Rejected. Both channels settled 2026-09-08 |
| Full calendar recurrence rules | "Last Friday of the month", end dates, counts | Parsing and testing out of proportion to V1 | Rejected by the user, 2026-09-23 |
| Presets only, no interval | Cheapest recurrence | Cannot say "every 2 weeks" or "weekdays" | Rejected by the user, 2026-09-23 |
| Calendar export or subscription | Reminders in the user's own calendar app | A third-party integration, a V1 non-goal | Not V1 |

## Risks and unknowns

| Risk | Likelihood | Impact | What would tell us early |
|---|---|---|---|
| A reminder fires late or never, and nobody notices | medium | high | A fire-delay metric and an alert on missed fires, from launch |
| Duplicate notifications after a retry or restart | medium | medium | A delivered-count per reminder above one per channel |
| Reminder emails land in spam | medium | high | Open and bounce rates; one test to a common free mailbox before launch |
| Repeat phrases are misread | medium | medium | Edits to recurrence right after capture |
| Clock and timezone changes shift a reminder by an hour | medium | medium | Tests that cross a clock change in a zone that has one |
| Email cost grows with users | low | low | Emails per user per week against the per-send price |

## Open questions

All ten answered by the user on 2026-09-23, each as the recommended option offered.

| # | Question | Blocks | Owner | Answer |
|---|---|---|---|---|
| ~~Q1~~ | Does Records get a Reminders filter? Source §11 omits one | PRD | user | **Yes.** Its own filter, and listed under All |
| ~~Q2~~ | After a timezone change, what happens to reminders already set? | PRD | user | **Split by type.** A recurring reminder keeps its wall-clock time in the new zone. A one-time reminder keeps its original instant, consistent with 001 FR-28 |
| ~~Q3~~ | If Slashit is down at fire time, what happens once it is back? | PRD | user | **Deliver late, marked late, up to 24 hours.** Past 24 hours it shows in the app as missed and sends no email |
| ~~Q4~~ | What can the user do from the email? | PRD, build plan | user | **Link into the app only.** No action works from the email without signing in |
| ~~Q5~~ | Which snooze choices? | PRD, design | user | **10 minutes, 1 hour, tomorrow at the default reminder time** |
| ~~Q6~~ | What history does record detail show? | PRD | user | **Next fire time, last fired, and the action taken on it** (done, snoozed, missed). No full log |
| ~~Q7~~ | How do the channel switches behave? | PRD | user | **The in-app notification list always records.** The switches turn off the live pop-up and the email. Settings warns once when both are off |
| ~~Q8~~ | "7pm" said at 8pm? | PRD | user | **The next 7pm**, shown as "Tomorrow, 7:00 PM" in the confirmation. No question asked |
| ~~Q9~~ | Per-user caps? | PRD | user | **100 active reminders, 50 reminder emails a day**, `estimate`, revisited with real usage. Past the email cap, the in-app list still records |
| ~~Q10~~ | State of a fired one-time reminder nobody acted on? | PRD | user | **Stays open until acted on.** Listed as fired and not done, notification unread, until marked done or snoozed |

## What this is not

- Not task alerts. A task's due date does not notify in this epic.
- Not push notifications, SMS, or any channel other than in-app and email.
- Not calendar recurrence rules: no "last Friday", no end dates, no counts, no
  per-occurrence edits.
- Not calendar sync, export or subscription.
- Not quiet hours, digests or batching. One reminder, one notification.
- Not proactive suggestions. Slashit notifies only for reminders the user set.
- Not reminders for other people. The user reminds only themselves.

## Change log

| Date | Change | Why | Approved by |
|---|---|---|---|
| 2026-09-23 | Created, with the user's four scoping answers recorded | User asked to proceed with epic 003 | user |
| 2026-09-23 | Q1 to Q10 answered and closed; requirement notes updated to match | User answered all ten, each as the recommended option | user |
| 2026-09-23 | Approved | User: "epic approved, write the prd" | user |
