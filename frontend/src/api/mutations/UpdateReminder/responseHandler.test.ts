import { describe, expect, it, vi } from "vitest";

import { buildReminder } from "../../../testing/reminderFixture";
import type { UpdateReminderMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("UpdateReminder responseHandler", () => {
  it("hands the updated reminder to onReminderUpdated", () => {
    const { handleResponse } = useResponseHandler();
    const onReminderUpdated = vi.fn();
    const reminder = { __typename: "Reminder" as const, ...buildReminder() };

    handleResponse({ data: { updateReminder: reminder }, onReminderUpdated });

    expect(onReminderUpdated).toHaveBeenCalledWith(reminder);
  });

  it("names the refused field for InvalidReminder", () => {
    const { handleResponse } = useResponseHandler();
    const onInvalidReminder = vi.fn();
    const data: UpdateReminderMutation = {
      updateReminder: {
        __typename: "InvalidReminder",
        field: "repeatWeekdays",
        message: "Pick at least one day.",
      },
    };

    handleResponse({ data, onInvalidReminder });

    expect(onInvalidReminder).toHaveBeenCalledWith({
      field: "repeatWeekdays",
      message: "Pick at least one day.",
    });
  });

  it.each([
    ["ReminderTimePassed", "onReminderTimePassed"],
    ["ReminderDeleted", "onReminderDeleted"],
    ["ReminderNotFound", "onReminderNotFound"],
  ] as const)("routes %s to %s with its message", (typename, callbackName) => {
    const { handleResponse } = useResponseHandler();
    const callback = vi.fn();
    const data = { updateReminder: { __typename: typename, message: "said" } } as UpdateReminderMutation;

    handleResponse({ data, [callbackName]: callback });

    expect(callback).toHaveBeenCalledWith("said");
  });

  it("throws on a member it does not know, rather than dropping it", () => {
    const { handleResponse } = useResponseHandler();
    const data = { updateReminder: { __typename: "Unknown" } } as unknown as UpdateReminderMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled UpdateReminderResult type");
  });
});
