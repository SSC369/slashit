/**
 * Calendar dates as ISO strings ("2026-10-03"), with no time and no zone. An
 * expense's `spentOn` is a day, not an instant, so these never pass through
 * the browser's timezone: the arithmetic is done in UTC.
 */

const WEEKDAYS_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const WEEKDAYS_LONG = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_LONG = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const pad = (value: number): string => String(value).padStart(2, "0");

const toUtc = (iso: string): Date => {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
};

const fromUtc = (date: Date): string =>
  `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`;

/** The browser's local today. */
export const todayIso = (): string => {
  const now = new Date();
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
};

export const addDays = (iso: string, days: number): string => {
  const date = toUtc(iso);
  date.setUTCDate(date.getUTCDate() + days);
  return fromUtc(date);
};

/** The same day in another month, held to that month's last day: 31 Jan + 1 is 28 Feb. */
export const addMonths = (iso: string, months: number): string => {
  const date = toUtc(iso);
  const day = date.getUTCDate();
  const target = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + months, 1));
  const lastDay = new Date(Date.UTC(target.getUTCFullYear(), target.getUTCMonth() + 1, 0)).getUTCDate();
  target.setUTCDate(Math.min(day, lastDay));
  return fromUtc(target);
};

/** "Sat 10 Oct", as design §8 writes a date in a sentence. */
export const formatDayShort = (iso: string): string => {
  const date = toUtc(iso);
  return `${WEEKDAYS_SHORT[date.getUTCDay()]} ${date.getUTCDate()} ${MONTHS_SHORT[date.getUTCMonth()]}`;
};

/** "Saturday 3 October 2026", the calendar's chosen date. */
export const formatDayLong = (iso: string): string => {
  const date = toUtc(iso);
  return `${WEEKDAYS_LONG[date.getUTCDay()]} ${date.getUTCDate()} ${MONTHS_LONG[date.getUTCMonth()]} ${date.getUTCFullYear()}`;
};

/** "October 2026", the calendar's heading. */
export const formatMonthYear = (iso: string): string => {
  const date = toUtc(iso);
  return `${MONTHS_LONG[date.getUTCMonth()]} ${date.getUTCFullYear()}`;
};

/** The saved card's Date field: "Today", or "Thu 1 Oct". */
export const formatSpentOn = (iso: string, today: string): string =>
  iso === today ? "Today" : formatDayShort(iso);

/**
 * The weeks of the month holding `iso`, Monday first (PRD assumption), padded
 * with the days of the months either side so every week has seven.
 */
export const monthGrid = (iso: string): string[][] => {
  const date = toUtc(iso);
  const first = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
  const mondayOffset = (first.getUTCDay() + 6) % 7;
  const lastDay = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0)).getUTCDate();
  const cellCount = Math.ceil((mondayOffset + lastDay) / 7) * 7;
  const start = addDays(fromUtc(first), -mondayOffset);
  const weeks: string[][] = [];
  for (let index = 0; index < cellCount; index += 7) {
    weeks.push(Array.from({ length: 7 }, (_, day) => addDays(start, index + day)));
  }
  return weeks;
};

export const isSameMonth = (left: string, right: string): boolean => left.slice(0, 7) === right.slice(0, 7);

export const dayOfMonth = (iso: string): number => toUtc(iso).getUTCDate();

/** "Thu 1 Oct 2026", the edit form's date field. */
export const formatDayShortWithYear = (iso: string): string => `${formatDayShort(iso)} ${toUtc(iso).getUTCFullYear()}`;
