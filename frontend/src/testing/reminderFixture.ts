import type { ReminderFieldsFragment } from "../fragments/ReminderFields.generated";

/** One reminder as the API returns it; tests override what they assert on. */
export const buildReminder = (overrides: Partial<ReminderFieldsFragment> = {}): ReminderFieldsFragment => ({
  id: "r0",
  description: "Call Mom",
  state: "UPCOMING",
  nextFireAt: "2026-09-24T13:30:00Z",
  whenText: "Tomorrow, 7:00 PM",
  repeatText: "Does not repeat",
  repeatKind: "NONE",
  repeatInterval: 1,
  repeatWeekdays: [],
  repeatMonthDay: null,
  localTime: "19:00",
  anchorLocalDate: "2026-09-24",
  scheduleTimezone: "Asia/Kolkata",
  lastFiredAt: null,
  lastAction: null,
  origin: "command",
  originalInput: "/remind Call Mom tomorrow at 7pm",
  createdAt: "2026-09-23T04:30:00Z",
  updatedAt: "2026-09-23T04:30:00Z",
  whenNote: null,
  ...overrides,
});
