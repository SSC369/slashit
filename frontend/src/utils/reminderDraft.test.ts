import { describe, expect, it } from "vitest";

import { describeDraftSchedule, validateDraft, type ReminderDraft } from "./reminderDraft";

const draft = (overrides: Partial<ReminderDraft>): ReminderDraft => ({
  description: "Standup notes",
  startDate: "2026-09-24",
  localTime: "09:30",
  repeatKind: "WEEKLY",
  repeatInterval: 1,
  repeatWeekdays: [0, 1, 2, 3, 4],
  ...overrides,
});

describe("reminderDraft", () => {
  it("reads the draft back in the design's words", () => {
    expect(describeDraftSchedule(draft({}), "Asia/Kolkata")).toBe(
      "Every weekday at 9:30 AM, Asia/Kolkata. Changes apply to every future occurrence.",
    );
    expect(
      describeDraftSchedule(
        draft({ repeatKind: "NONE", startDate: "2026-09-23", localTime: "07:00" }),
        "Asia/Kolkata",
      ),
    ).toBe("Once, Wed 23 Sep at 7:00 AM, Asia/Kolkata.");
    expect(describeDraftSchedule(draft({ repeatWeekdays: [] }), "Asia/Kolkata")).toBe(
      "Weekly at 9:30 AM, Asia/Kolkata. Pick a day to see the schedule.",
    );
    expect(
      describeDraftSchedule(draft({ repeatKind: "MONTHLY", startDate: "2026-10-31" }), "UTC"),
    ).toBe("Every month on the 31st at 9:30 AM, UTC. Changes apply to every future occurrence.");
  });

  it("names the fields the server would refuse, in its words", () => {
    expect(validateDraft(draft({ description: "  ", repeatWeekdays: [] }))).toEqual({
      description: "Give the reminder a name.",
      repeatWeekdays: "Pick at least one day.",
    });
    expect(validateDraft(draft({}))).toEqual({});
  });
});
