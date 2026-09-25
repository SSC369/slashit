import { describe, expect, it, vi } from "vitest";

import type { DeleteReminderMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("DeleteReminder responseHandler", () => {
  it("hands the deleted id to onReminderDeleted", () => {
    const { handleResponse } = useResponseHandler();
    const onReminderDeleted = vi.fn();
    const data: DeleteReminderMutation = {
      deleteReminder: { __typename: "ReminderDeleteSucceeded", id: "r1" },
    };

    handleResponse({ data, onReminderDeleted });

    expect(onReminderDeleted).toHaveBeenCalledWith("r1");
  });

  it("calls onReminderNotFound for another user's or a missing id", () => {
    const { handleResponse } = useResponseHandler();
    const onReminderNotFound = vi.fn();
    const data: DeleteReminderMutation = {
      deleteReminder: { __typename: "ReminderNotFound", message: "gone" },
    };

    handleResponse({ data, onReminderNotFound });

    expect(onReminderNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { deleteReminder: { __typename: "Unknown" } } as unknown as DeleteReminderMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled DeleteReminderResult type");
  });
});
