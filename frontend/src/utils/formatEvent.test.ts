import { describe, expect, it } from "vitest";

import { buildEvent } from "../testing/eventFixture";
import {
  dateBoxParts,
  dayLabel,
  detailWhen,
  formatEventStart,
  formatTimeRange,
  localToday,
  monthHeading,
  multiDayLength,
  timedLength,
} from "./formatEvent";

describe("formatEvent", () => {
  it("reads today in the event's zone, not the browser's", () => {
    expect(localToday("Asia/Kolkata", new Date("2026-10-01T20:00:00Z"))).toBe("2026-10-02");
    expect(localToday("America/New_York", new Date("2026-10-01T20:00:00Z"))).toBe("2026-10-01");
  });

  it("labels days as the server does", () => {
    expect(dayLabel("2026-10-02", "2026-10-02")).toBe("Today");
    expect(dayLabel("2026-10-03", "2026-10-02")).toBe("Tomorrow");
    expect(dayLabel("2026-10-12", "2026-10-02")).toBe("Mon 12 Oct");
    expect(dayLabel("2019-06-14", "2026-10-02")).toBe("Fri 14 Jun 2019");
  });

  it("gives the All tab the start alone", () => {
    const now = new Date("2026-10-02T04:00:00Z");
    expect(formatEventStart(buildEvent(), now)).toBe("Mon 12 Oct");
    expect(
      formatEventStart(buildEvent({ occurrenceDate: "2026-10-02", startTime: "14:00", allDay: false }), now),
    ).toBe("Today, 2:00 PM");
  });

  it("draws the date box and month heading from the calendar day", () => {
    expect(dateBoxParts("2026-10-12")).toEqual({ day: "12", weekday: "Mon", spoken: "Monday 12 October" });
    expect(monthHeading("2026-11-21")).toBe("November 2026");
  });

  it("drops the first meridiem only when both share it", () => {
    expect(formatTimeRange("16:00", "17:00")).toBe("4:00 to 5:00 PM");
    expect(formatTimeRange("23:00", "01:00")).toBe("11:00 PM to 1:00 AM");
  });

  it("counts an all-day range inclusively and a timed event by its length", () => {
    const trip = buildEvent({ occurrenceDate: "2026-12-20", occurrenceEndDate: "2026-12-24" });
    expect(multiDayLength(trip)).toBe("5 days");
    expect(multiDayLength(buildEvent())).toBeNull();
    const dentist = buildEvent({
      allDay: false,
      startTime: "16:00",
      endTime: "17:30",
      startsAt: "2026-10-09T10:30:00Z",
      endsAt: "2026-10-09T12:00:00Z",
    });
    expect(timedLength(dentist)).toBe("1 hour 30 minutes");
  });

  it("gives the detail its year", () => {
    expect(detailWhen(buildEvent())).toBe("Mon 12 Oct 2026");
    expect(
      detailWhen(
        buildEvent({ occurrenceDate: "2026-10-09", occurrenceEndDate: "2026-10-09", startTime: "16:00", endTime: "17:00", allDay: false }),
      ),
    ).toBe("Fri 9 Oct 2026, 4:00 to 5:00 PM");
  });
});
