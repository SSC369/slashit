import { describe, expect, it, vi } from "vitest";

import { useResponseHandler } from "./responseHandler";
import type { UpdateReminderSettingsMutation } from "./operation.generated";

const SAVED_SETTINGS = {
  timezone: "Asia/Kolkata",
  defaultReminderTime: "09:00",
  popupsEnabled: false,
  emailEnabled: false,
};

describe("UpdateReminderSettings responseHandler", () => {
  it("calls onReminderSettingsSaved with the settings and the warning flag", () => {
    const { handleResponse } = useResponseHandler();
    const onReminderSettingsSaved = vi.fn();
    const data: UpdateReminderSettingsMutation = {
      updateReminderSettings: {
        __typename: "ReminderSettingsSaved",
        showBothOffWarning: true,
        settings: SAVED_SETTINGS,
      },
    };

    handleResponse({ data, onReminderSettingsSaved });

    expect(onReminderSettingsSaved).toHaveBeenCalledWith({
      settings: SAVED_SETTINGS,
      showBothOffWarning: true,
    });
  });

  it("calls onInvalidReminderSettings with the message and field", () => {
    const { handleResponse } = useResponseHandler();
    const onInvalidReminderSettings = vi.fn();
    const data: UpdateReminderSettingsMutation = {
      updateReminderSettings: {
        __typename: "InvalidReminderSettings",
        message: "Pick a time.",
        field: "defaultReminderTime",
      },
    };

    handleResponse({ data, onInvalidReminderSettings });

    expect(onInvalidReminderSettings).toHaveBeenCalledWith({
      message: "Pick a time.",
      field: "defaultReminderTime",
    });
  });

  it("throws via assertNever for an unhandled typename", () => {
    const { handleResponse } = useResponseHandler();
    const data = {
      updateReminderSettings: { __typename: "SomethingNew" },
    } as unknown as UpdateReminderSettingsMutation;

    expect(() => handleResponse({ data })).toThrow(/Unhandled UpdateReminderSettingsResult type/);
  });
});
