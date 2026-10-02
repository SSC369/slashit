import type { EventFieldsFragment } from "../fragments/EventFields.generated";
import { formatCalendarDate, formatClockTime } from "./formatReminder";

const DAY_MS = 86_400_000;

/** A calendar day, "2026-10-12", as a UTC instant at noon: weekday and month
 * read from it never shift with the browser's zone. */
const noonOf = (localDate: string): Date => new Date(`${localDate}T12:00:00Z`);

const UTC_PARTS = new Intl.DateTimeFormat("en-US", {
  timeZone: "UTC",
  weekday: "short",
  day: "numeric",
  month: "short",
  year: "numeric",
});

const MONTH_YEAR = new Intl.DateTimeFormat("en-US", { timeZone: "UTC", month: "long", year: "numeric" });

const partsOf = (localDate: string): Record<string, string> => {
  const parts: Record<string, string> = {};
  for (const part of UTC_PARTS.formatToParts(noonOf(localDate))) parts[part.type] = part.value;
  return parts;
};

/** Today in the event's own zone, "2026-10-02". */
export const localToday = (timeZone: string, now: Date = new Date()): string =>
  new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(now);

const daysBetween = (fromDate: string, toDate: string): number =>
  Math.round((noonOf(toDate).getTime() - noonOf(fromDate).getTime()) / DAY_MS);

/** The date box (design §6 `.datebox`): "12" over "Mon". Read in full by a
 * screen reader as "Monday 12 October" (design §7). */
export const dateBoxParts = (localDate: string): { day: string; weekday: string; spoken: string } => {
  const parts = partsOf(localDate);
  const spoken = new Intl.DateTimeFormat("en-GB", {
    timeZone: "UTC",
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(noonOf(localDate));
  return { day: parts.day ?? "", weekday: parts.weekday ?? "", spoken: spoken.replace(",", "") };
};

/** `/events` month heading: "October 2026". */
export const monthHeading = (localDate: string): string => MONTH_YEAR.format(noonOf(localDate));

/** "Today", "Tomorrow", "Mon 12 Oct", or "Fri 14 Jun 2019" in another year,
 * as the server's When line spells a day. */
export const dayLabel = (localDate: string, today: string): string => {
  const offset = daysBetween(today, localDate);
  if (offset === 0) return "Today";
  if (offset === 1) return "Tomorrow";
  const parts = partsOf(localDate);
  const label = `${parts.weekday} ${parts.day} ${parts.month}`;
  return localDate.slice(0, 4) === today.slice(0, 4) ? label : `${label} ${parts.year}`;
};

/** The All tab's Date column (`RecordsAllEvents`): the start alone,
 * "Today, 2:00 PM" or "Mon 12 Oct". */
export const formatEventStart = (event: EventFieldsFragment, now: Date = new Date()): string => {
  const day = dayLabel(event.occurrenceDate, localToday(event.scheduleTimezone, now));
  return event.startTime === null ? day : `${day}, ${formatClockTime(event.startTime)}`;
};

/** "4:00 to 5:00 PM", or "11:00 PM to 1:00 AM" across a meridiem. */
export const formatTimeRange = (startTime: string, endTime: string): string => {
  const start = formatClockTime(startTime);
  const end = formatClockTime(endTime);
  return start.slice(-2) === end.slice(-2) ? `${start.slice(0, -3)} to ${end}` : `${start} to ${end}`;
};

const isMultiDay = (event: EventFieldsFragment): boolean => event.occurrenceEndDate !== event.occurrenceDate;

/** "5 days" for an all-day range, counting both ends (design `EventResolvedMore`). */
export const multiDayLength = (event: EventFieldsFragment): string | null => {
  if (!event.allDay || !isMultiDay(event)) return null;
  const days = daysBetween(event.occurrenceDate, event.occurrenceEndDate) + 1;
  return `${days} days`;
};

/** "1 hour", "1 hour 30 minutes", "45 minutes" for a timed event with an end. */
export const timedLength = (event: EventFieldsFragment): string | null => {
  if (event.allDay || event.endTime === null) return null;
  const minutes = Math.round((new Date(event.endsAt).getTime() - new Date(event.startsAt).getTime()) / 60_000);
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  const hourText = hours > 0 ? `${hours} ${hours === 1 ? "hour" : "hours"}` : "";
  const minuteText = rest > 0 ? `${rest} ${rest === 1 ? "minute" : "minutes"}` : "";
  return [hourText, minuteText].filter((text) => text !== "").join(" ");
};

/** The detail's When or Next value, with the year (`EventDetail`): "Mon 12 Oct
 * 2026" or "Fri 9 Oct 2026, 4:00 to 5:00 PM". A range keeps the server's line. */
export const detailWhen = (event: EventFieldsFragment): string => {
  if (isMultiDay(event) && (event.allDay || event.endTime === null)) return event.whenText;
  const date = formatCalendarDate(event.occurrenceDate);
  if (event.startTime === null) return date;
  if (event.endTime === null) return `${date}, ${formatClockTime(event.startTime)}`;
  if (isMultiDay(event) && daysBetween(event.occurrenceDate, event.occurrenceEndDate) > 1) return event.whenText;
  return `${date}, ${formatTimeRange(event.startTime, event.endTime)}`;
};

/** "12 Oct", for "stays on 12 Oct" and "On 12 Oct". */
export const dayMonth = (localDate: string): string => {
  const parts = partsOf(localDate);
  return `${parts.day} ${parts.month}`;
};
