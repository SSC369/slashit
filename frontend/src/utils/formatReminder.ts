import type { ReminderFieldsFragment } from "../fragments/ReminderFields.generated";

/** The server's weekday numbering: 0 is Monday, as Python's `weekday()`. */
export const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] as const;

const WEEKDAYS_MON_TO_FRI = [0, 1, 2, 3, 4];

export type ReminderStatusToneType = "UPCOMING" | "FIRED" | "MISSED" | "DONE";

interface ZonedParts {
  weekday: string;
  day: string;
  month: string;
  year: string;
  hour: string;
  minute: string;
  dayPeriod: string;
}

/** Parts in the reminder's own zone, assembled by hand so a locale's own
 * spelling ("Sept") never replaces the design's ("Sep"). */
const zonedParts = (instant: string, timeZone: string): ZonedParts => {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone,
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
  const parts: Record<string, string> = {};
  for (const part of formatter.formatToParts(new Date(instant))) {
    parts[part.type] = part.value;
  }
  return {
    weekday: parts.weekday ?? "",
    day: parts.day ?? "",
    month: parts.month ?? "",
    year: parts.year ?? "",
    hour: parts.hour ?? "",
    minute: parts.minute ?? "",
    dayPeriod: (parts.dayPeriod ?? "").toUpperCase(),
  };
};

/** "Wed 24 Sep 2026", in the reminder's zone. */
export const formatReminderDate = (instant: string, timeZone: string): string => {
  const parts = zonedParts(instant, timeZone);
  return `${parts.weekday} ${parts.day} ${parts.month} ${parts.year}`;
};

/** "Wed 24 Sep, 9:00 AM", in the reminder's zone. */
export const formatReminderDateTime = (instant: string, timeZone: string): string => {
  const parts = zonedParts(instant, timeZone);
  return `${parts.weekday} ${parts.day} ${parts.month}, ${parts.hour}:${parts.minute} ${parts.dayPeriod}`;
};

/** "9:30 AM" from the API's "09:30". */
export const formatClockTime = (localTime: string): string => {
  const [hourText, minuteText] = localTime.split(":");
  const hour = Number(hourText);
  const hour12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${hour12}:${minuteText} ${hour < 12 ? "AM" : "PM"}`;
};

/** "Wed 24 Sep 2026" from an anchor date, "2026-09-24", read as a calendar
 * day with no zone at all. */
export const formatCalendarDate = (localDate: string): string =>
  formatReminderDate(`${localDate}T12:00:00Z`, "UTC");

/** "Mon to Fri", or the days in order: "Mon, Wed, Fri". */
export const describeWeekdays = (weekdays: readonly number[]): string => {
  const sorted = [...weekdays].sort((left, right) => left - right);
  const isMonToFri =
    sorted.length === WEEKDAYS_MON_TO_FRI.length &&
    sorted.every((day, index) => day === WEEKDAYS_MON_TO_FRI[index]);
  if (isMonToFri) return "Mon to Fri";
  return sorted.map((day) => WEEKDAY_LABELS[day] ?? "").join(", ");
};

/** The small line under a repeat value, or null when the value says it all:
 * "Mon to Fri" for a weekly rule, the month-end rule for a day past the 28th. */
export const describeRepeatDetail = (reminder: ReminderFieldsFragment): string | null => {
  if (reminder.repeatKind === "WEEKLY" && reminder.repeatWeekdays.length > 0) {
    return describeWeekdays(reminder.repeatWeekdays);
  }
  const monthDay = reminder.repeatMonthDay;
  const isPastShortestMonth = monthDay !== null && monthDay > 28;
  if (reminder.repeatKind === "MONTHLY" && isPastShortestMonth) {
    return "Or the last day, in shorter months";
  }
  return null;
};

/** "tomorrow, 7:00 PM" inside a sentence; a date keeps its capital. */
export const whenTextInSentence = (whenText: string): string => {
  const isRelativeDay = whenText.startsWith("Today") || whenText.startsWith("Tomorrow");
  return isRelativeDay ? whenText.charAt(0).toLowerCase() + whenText.slice(1) : whenText;
};

export const reminderStatusTone = (reminder: ReminderFieldsFragment): ReminderStatusToneType => {
  if (reminder.state === "DONE") return "DONE";
  if (reminder.state === "FIRED") return reminder.lastAction === "MISSED" ? "MISSED" : "FIRED";
  return "UPCOMING";
};

export const REMINDER_STATUS_LABEL: Record<ReminderStatusToneType, string> = {
  UPCOMING: "Upcoming",
  FIRED: "Fired, not done",
  MISSED: "Missed",
  DONE: "Done",
};

export const REMINDER_ACTION_LABEL: Record<NonNullable<ReminderFieldsFragment["lastAction"]>, string> = {
  DONE: "Marked done",
  SNOOZED: "Snoozed",
  MISSED: "Missed",
};
