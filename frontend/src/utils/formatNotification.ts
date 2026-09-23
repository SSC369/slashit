import type { NotificationFieldsFragment } from "../fragments/NotificationFields.generated";
import { formatClockTime } from "./formatReminder";

const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MINUTE_MS = 60_000;

const isSameLocalDay = (left: Date, right: Date): boolean =>
  left.getFullYear() === right.getFullYear() &&
  left.getMonth() === right.getMonth() &&
  left.getDate() === right.getDate();

/** "7:00 PM", in the viewer's own clock. */
export const formatInstantClock = (instant: Date): string => {
  const hours = String(instant.getHours()).padStart(2, "0");
  const minutes = String(instant.getMinutes()).padStart(2, "0");
  return formatClockTime(`${hours}:${minutes}`);
};

/** "Today, 10:00 AM", or "Sat 20 Sep, 11:00 AM". */
export const formatDayAndClock = (instant: Date, now: Date): string => {
  if (isSameLocalDay(instant, now)) return `Today, ${formatInstantClock(instant)}`;
  return `${WEEKDAYS[instant.getDay()]} ${instant.getDate()} ${MONTHS[instant.getMonth()]}, ${formatInstantClock(instant)}`;
};

/** "Sun 6:00 PM": the short form the Late line uses for both times. */
const formatWeekdayAndClock = (instant: Date): string =>
  `${WEEKDAYS[instant.getDay()]} ${formatInstantClock(instant)}`;

/** The grey line under a panel item (`NotificationPanel`). */
export const describeNotificationMeta = (
  notification: NotificationFieldsFragment,
  now: Date,
): string => {
  const due = new Date(notification.occurredAt);
  if (notification.marker === "MISSED") {
    return `Reminder · due ${formatDayAndClock(due, now)}. Slashit could not deliver it in time, so no email was sent`;
  }
  if (notification.marker === "LATE") {
    const delivered = new Date(notification.createdAt);
    return `Reminder · due ${formatWeekdayAndClock(due)}, delivered ${formatWeekdayAndClock(delivered)}`;
  }
  const parts = [`Reminder · ${formatDayAndClock(due, now)}`];
  if (notification.detail) parts.push(notification.detail.charAt(0).toLowerCase() + notification.detail.slice(1));
  if (notification.action !== null && notification.actedAt !== null) {
    const verb = notification.action === "DONE" ? "marked done" : "snoozed";
    parts.push(`${verb} ${formatInstantClock(new Date(notification.actedAt))}`);
  }
  return parts.join(" · ");
};

export type SnoozeOptionType = "TEN_MINUTES" | "ONE_HOUR" | "TOMORROW";

export interface SnoozeChoice {
  option: SnoozeOptionType;
  label: string;
  resultingTime: string;
}

/** FR-21's three choices, each with the time it lands on (`ReminderToast`). */
export const buildSnoozeChoices = (now: Date, defaultReminderTime: string | null): SnoozeChoice[] => [
  {
    option: "TEN_MINUTES",
    label: "10 minutes",
    resultingTime: formatInstantClock(new Date(now.getTime() + 10 * MINUTE_MS)),
  },
  {
    option: "ONE_HOUR",
    label: "1 hour",
    resultingTime: formatInstantClock(new Date(now.getTime() + 60 * MINUTE_MS)),
  },
  {
    option: "TOMORROW",
    label: "Tomorrow",
    resultingTime: defaultReminderTime !== null ? formatClockTime(defaultReminderTime) : "",
  },
];
