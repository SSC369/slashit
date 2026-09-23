import { describe, expect, it, vi } from "vitest";

import { buildReminder } from "../../../testing/reminderFixture";
import type { GetReminderQuery } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("GetReminder responseHandler", () => {
  it("hands a found reminder to onReminderLoaded", () => {
    const { handleResponse } = useResponseHandler();
    const onReminderLoaded = vi.fn();
    const reminder = { __typename: "Reminder" as const, ...buildReminder() };

    handleResponse({ data: { reminder }, onReminderLoaded });

    expect(onReminderLoaded).toHaveBeenCalledWith(reminder);
  });

  it("calls onReminderNotFound for ReminderNotFound", () => {
    const { handleResponse } = useResponseHandler();
    const onReminderNotFound = vi.fn();
    const data: GetReminderQuery = { reminder: { __typename: "ReminderNotFound", message: "gone" } };

    handleResponse({ data, onReminderNotFound });

    expect(onReminderNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { reminder: { __typename: "Unknown" } } as unknown as GetReminderQuery;

    expect(() => handleResponse({ data })).toThrow("Unhandled ReminderResult type");
  });
});
