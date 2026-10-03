import { describe, expect, it } from "vitest";

import { addDays, addMonths, formatDayLong, formatDayShort, formatSpentOn, monthGrid } from "./localDate";

describe("localDate", () => {
  it("formats as design §8 writes dates", () => {
    expect(formatDayShort("2026-10-10")).toBe("Sat 10 Oct");
    expect(formatDayLong("2026-10-03")).toBe("Saturday 3 October 2026");
    expect(formatSpentOn("2026-10-02", "2026-10-02")).toBe("Today");
    expect(formatSpentOn("2026-10-01", "2026-10-02")).toBe("Thu 1 Oct");
  });

  it("moves across month and year ends", () => {
    expect(addDays("2026-12-31", 1)).toBe("2027-01-01");
    expect(addDays("2026-03-01", -1)).toBe("2026-02-28");
    expect(addMonths("2026-01-31", 1)).toBe("2026-02-28");
    expect(addMonths("2026-01-15", -1)).toBe("2025-12-15");
  });

  it("lays out October 2026 Monday first, as DatePick draws it", () => {
    const weeks = monthGrid("2026-10-10");
    expect(weeks[0]).toEqual([
      "2026-09-28",
      "2026-09-29",
      "2026-09-30",
      "2026-10-01",
      "2026-10-02",
      "2026-10-03",
      "2026-10-04",
    ]);
    expect(weeks).toHaveLength(5);
    expect(weeks[4][6]).toBe("2026-11-01");
  });
});
