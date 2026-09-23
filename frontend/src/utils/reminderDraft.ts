import type { ReminderFieldsFragment } from "../fragments/ReminderFields.generated";
import { WEEKDAY_LABELS, describeWeekdays, formatClockTime } from "./formatReminder";

export type RepeatKindType = ReminderFieldsFragment["repeatKind"];

/** What the edit form holds (FR-28). Mirrors UpdateReminderInput. */
export interface ReminderDraft {
  description: string;
  /** YYYY-MM-DD, a day in the reminder's own zone. */
  startDate: string;
  /** HH:MM, 24-hour. */
  localTime: string;
  repeatKind: RepeatKindType;
  repeatInterval: number;
  repeatWeekdays: number[];
}

/** Field name, as the server's InvalidReminder.field names it, to message. */
export type ReminderFieldErrors = Partial<Record<keyof ReminderDraft, string>>;

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const INTERVAL_UNITS: Record<Exclude<RepeatKindType, "NONE">, [string, string]> = {
  DAILY: ["day", "days"],
  WEEKLY: ["week", "weeks"],
  MONTHLY: ["month", "months"],
  YEARLY: ["year", "years"],
};

export const draftFromReminder = (reminder: ReminderFieldsFragment): ReminderDraft => ({
  description: reminder.description,
  startDate: reminder.anchorLocalDate,
  localTime: reminder.localTime,
  repeatKind: reminder.repeatKind,
  repeatInterval: reminder.repeatInterval,
  repeatWeekdays: [...reminder.repeatWeekdays],
});

/** The checks the server makes that the form can make first, with the
 * server's own words, so Save can be disabled before a round trip. */
export const validateDraft = (draft: ReminderDraft): ReminderFieldErrors => {
  const errors: ReminderFieldErrors = {};
  if (draft.description.trim() === "") errors.description = "Give the reminder a name.";
  if (draft.repeatKind === "WEEKLY" && draft.repeatWeekdays.length === 0) {
    errors.repeatWeekdays = "Pick at least one day.";
  }
  return errors;
};

/** The unit after the interval box: "week" for 1, "weeks" for more. */
export const describeIntervalUnit = (
  kind: Exclude<RepeatKindType, "NONE">,
  interval: number,
): string => {
  const [singular, plural] = INTERVAL_UNITS[kind];
  return interval === 1 ? singular : plural;
};

const ordinal = (day: number): string => {
  const lastTwo = day % 100;
  if (lastTwo >= 11 && lastTwo <= 13) return `${day}th`;
  const suffix = { 1: "st", 2: "nd", 3: "rd" }[day % 10] ?? "th";
  return `${day}${suffix}`;
};

/** Parts of a YYYY-MM-DD read as a calendar day, never shifted by a zone. */
const calendarParts = (localDate: string): { weekday: string; day: number; month: string } => {
  const [year, month, day] = localDate.split("-").map(Number);
  const weekdayIndex = (new Date(Date.UTC(year, month - 1, day)).getUTCDay() + 6) % 7;
  return { weekday: WEEKDAY_LABELS[weekdayIndex], day, month: MONTH_LABELS[month - 1] ?? "" };
};

const describeRepeatRule = (draft: ReminderDraft): string => {
  const interval = draft.repeatInterval;
  const start = calendarParts(draft.startDate);
  switch (draft.repeatKind) {
    case "NONE":
      return `Once, ${start.weekday} ${start.day} ${start.month}`;
    case "DAILY":
      return interval === 1 ? "Every day" : `Every ${interval} days`;
    case "WEEKLY": {
      const days = describeWeekdays(draft.repeatWeekdays);
      if (interval === 1 && days === "Mon to Fri") return "Every weekday";
      return interval === 1 ? `Every week on ${days}` : `Every ${interval} weeks on ${days}`;
    }
    case "MONTHLY":
      return interval === 1
        ? `Every month on the ${ordinal(start.day)}`
        : `Every ${interval} months on the ${ordinal(start.day)}`;
    case "YEARLY":
      return interval === 1
        ? `Every year on ${start.day} ${start.month}`
        : `Every ${interval} years on ${start.day} ${start.month}`;
    default: {
      const unhandled: never = draft.repeatKind;
      throw new Error(`Unhandled repeat kind: ${String(unhandled)}`);
    }
  }
};

/** The line under the form that reads the draft back (`ReminderEdit`):
 * "Every weekday at 9:30 AM, Asia/Kolkata. Changes apply to every future
 * occurrence." */
export const describeDraftSchedule = (draft: ReminderDraft, timezone: string): string => {
  const clock = draft.localTime ? formatClockTime(draft.localTime) : "a time to pick";
  const isMissingDays = draft.repeatKind === "WEEKLY" && draft.repeatWeekdays.length === 0;
  if (isMissingDays) return `Weekly at ${clock}, ${timezone}. Pick a day to see the schedule.`;
  if (!draft.startDate) return `At ${clock}, ${timezone}. Pick a start date to see the schedule.`;
  const rule = describeRepeatRule(draft);
  if (draft.repeatKind === "NONE") return `${rule} at ${clock}, ${timezone}.`;
  return `${rule} at ${clock}, ${timezone}. Changes apply to every future occurrence.`;
};

/** A repeating reminder's detail line: "Mon to Fri, every week". */
export const describeRepeatCadence = (reminder: ReminderFieldsFragment): string | null => {
  if (reminder.repeatKind !== "WEEKLY" || reminder.repeatWeekdays.length === 0) return null;
  const every = reminder.repeatInterval === 1 ? "every week" : `every ${reminder.repeatInterval} weeks`;
  return `${describeWeekdays(reminder.repeatWeekdays)}, ${every}`;
};
