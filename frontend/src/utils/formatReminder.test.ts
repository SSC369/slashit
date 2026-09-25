import { describe, expect, it } from "vitest";

import {
  describeWeekdays,
  formatCalendarDate,
  formatClockTime,
  formatReminderDate,
  formatReminderDateTime,
  whenTextInSentence,
} from "./formatReminder";

describe("formatReminder", () => {
  it("reads an instant in the reminder's own zone, in the design's spelling", () => {
    // 04:00 UTC is 09:30 in Kolkata on the same day.
    expect(formatReminderDate("2026-09-24T04:00:00Z", "Asia/Kolkata")).toBe("Thu 24 Sep 2026");
    expect(formatReminderDateTime("2026-09-24T04:00:00Z", "Asia/Kolkata")).toBe("Thu 24 Sep, 9:30 AM");
  });

  it("formats a stored clock time and a calendar date", () => {
    expect(formatClockTime("09:30")).toBe("9:30 AM");
    expect(formatClockTime("19:00")).toBe("7:00 PM");
    expect(formatClockTime("00:05")).toBe("12:05 AM");
    expect(formatCalendarDate("2026-09-30")).toBe("Wed 30 Sep 2026");
  });

  it("names weekdays, Monday first", () => {
    expect(describeWeekdays([4, 3, 2, 1, 0])).toBe("Mon to Fri");
    expect(describeWeekdays([5, 0])).toBe("Mon, Sat");
  });

  it("lowercases only a relative day inside a sentence", () => {
    expect(whenTextInSentence("Tomorrow, 7:00 PM")).toBe("tomorrow, 7:00 PM");
    expect(whenTextInSentence("Wed 15 Oct, 9:00 AM")).toBe("Wed 15 Oct, 9:00 AM");
  });
});
