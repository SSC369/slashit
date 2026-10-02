import type { EventStatusType } from "../../types.generated";

/** Mirrors backend/app/domains/events/constants.py's MAX_UPCOMING_EVENTS (FR-31). */
export const MAX_UPCOMING_EVENTS = 500;

export interface EventAlertChoice {
  leadMinutes: number;
  label: string;
}

/** FR-16: nothing is saved until one of `choices`, or no alert, is picked. */
export interface EventAlertChoiceArgs {
  pendingCaptureId: string;
  question: string;
  choices: EventAlertChoice[];
}

/** The answer to FR-16's question that keeps no alert; the server's NO_ALERT_ANSWER. */
export const NO_ALERT_ANSWER = "none";

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
export const EVENT_ALERT_HINT = "An event can have one alert. The event is saved once you pick.";
export const EVENT_LIMIT_TITLE = `You have ${MAX_UPCOMING_EVENTS} upcoming events, the most Slashit holds.`;
export const EVENT_LIMIT_BODY =
  "Delete one you no longer need, then try again. What you typed is kept below. Past events do not count.";
export const EVENT_YEARLY_DETAIL_NOTE =
  "Editing changes every year's occurrence. The alert moves with the event and is shown only here, not under Reminders.";
export const EVENT_PAST_DETAIL_NOTE =
  "This event has passed. It is no longer listed by /events, and stays here in Records.";
export const EVENT_EXAMPLE_COMMAND = "/add-event Mom's birthday Oct 12";
