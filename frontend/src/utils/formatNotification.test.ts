import { describe, expect, it } from "vitest";

import type { NotificationFieldsFragment } from "../fragments/NotificationFields.generated";
import { buildSnoozeChoices, describeNotificationMeta } from "./formatNotification";

const local = (iso: string): string => new Date(iso).toISOString();

const notification = (overrides: Partial<NotificationFieldsFragment>): NotificationFieldsFragment => ({
  id: "n1",
  kind: "REMINDER",
  targetId: "r1",
  title: "Pay electricity bill",
  detail: "",
  marker: "NONE",
  occurredAt: local("2026-09-23T10:00:00"),
  createdAt: local("2026-09-23T10:00:05"),
  read: false,
  action: null,
  actedAt: null,
  showPopup: true,
  ...overrides,
});

describe("describeNotificationMeta", () => {
  const now = new Date("2026-09-23T12:00:00");

  it("reads an on-time firing with its repeat", () => {
    expect(describeNotificationMeta(notification({ detail: "Every month on the 23rd" }), now)).toBe(
      "Reminder · Today, 10:00 AM · every month on the 23rd",
    );
  });

  it("names what was done about it", () => {
    expect(
      describeNotificationMeta(
        notification({ action: "DONE", actedAt: local("2026-09-23T10:41:00") }),
        now,
      ),
    ).toBe("Reminder · Today, 10:00 AM · marked done 10:41 AM");
  });

  it("reads late and missed as the design writes them", () => {
    expect(
      describeNotificationMeta(
        notification({
          marker: "LATE",
          occurredAt: local("2026-09-20T18:00:00"),
          createdAt: local("2026-09-21T16:10:00"),
        }),
        now,
      ),
    ).toBe("Reminder · due Sun 6:00 PM, delivered Mon 4:10 PM");
    expect(
      describeNotificationMeta(
        notification({ marker: "MISSED", occurredAt: local("2026-09-19T11:00:00") }),
        now,
      ),
    ).toBe(
      "Reminder · due Sat 19 Sep, 11:00 AM. Slashit could not deliver it in time, so no email was sent",
    );
  });
});

describe("buildSnoozeChoices", () => {
  it("shows the time each choice lands on", () => {
    const choices = buildSnoozeChoices(new Date("2026-09-23T19:00:00"), "09:00");
    expect(choices.map((choice) => `${choice.label} ${choice.resultingTime}`)).toEqual([
      "10 minutes 7:10 PM",
      "1 hour 8:00 PM",
      "Tomorrow 9:00 AM",
    ]);
  });
});
