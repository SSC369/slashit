import type { AlertNotSetReason, EventStatusType } from "../../types.generated";
import type { EventFieldsFragment } from "../fragments/EventFields.generated";

/** Mirrors backend/app/domains/events/constants.py's MAX_UPCOMING_EVENTS (FR-31). */
export const MAX_UPCOMING_EVENTS = 500;

/** Mirrors backend/app/domains/reminders/constants.py's MAX_ACTIVE_REMINDERS (FR-33). */
export const MAX_ACTIVE_REMINDERS = 100;

/** FR-19 and FR-33: an alert asked for and not set. The event was saved. */
export interface EventAlertNotSet {
  leadMinutes: number;
  text: string;
  reason: AlertNotSetReason;
}

/** `EventCreated`: the event, and each alert it asked for that was not set. */
export interface EventCreatedArgs {
  event: EventFieldsFragment;
  alertsNotSet: EventAlertNotSet[];
}

/** `EventAsk`'s ready answers to "When is …?"; "Pick a date" opens a picker. */
export const EVENT_DATE_QUICK_ANSWERS: readonly string[] = ["Tomorrow", "This Saturday"];

/** The server's note under Repeat when "birthday" or "anniversary" set it (FR-9).
 * Every other note belongs under When. */
export const REPEAT_NOTE_PREFIX = "Read from";

export const EVENT_STATUS_LABEL: Record<EventStatusType, string> = {
  UPCOMING: "Upcoming",
  HAPPENING_NOW: "Happening now",
  PAST: "Past",
};

// Design §8 copy.
export const EVENT_DATE_HINT =
  "Reply with a date, and a time if there is one. Nothing is saved until you answer.";
export const EVENT_LIMIT_TITLE = `You have ${MAX_UPCOMING_EVENTS} upcoming events, the most Slashit holds.`;
export const EVENT_LIMIT_BODY =
  "Delete one you no longer need, then try again. What you typed is kept below. Past events do not count.";
export const EVENT_YEARLY_DETAIL_NOTE =
  "Editing changes every year's occurrence. Alerts move with the event and are shown only here, not under Reminders.";
export const EVENT_PAST_DETAIL_NOTE =
  "This event has passed. It is no longer listed by /events, and stays here in Records.";
export const EVENT_EXAMPLE_COMMAND = "/add-event Mom's birthday Oct 12";
