import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { API_INITIAL, API_SUCCESS } from "../../../../constants/apiConstants";
import { RootStore } from "../../../../stores/RootStore";
import { StoreProvider } from "../../../../stores/StoreProvider";
import SettingsController from "./SettingsController";

interface SaveArgs {
  input: { defaultReminderTime?: string; popupsEnabled?: boolean; emailEnabled?: boolean };
  onReminderSettingsSaved?: (args: {
    settings: {
      timezone: string;
      defaultReminderTime: string;
      popupsEnabled: boolean;
      emailEnabled: boolean;
    };
    showBothOffWarning: boolean;
  }) => void;
  onInvalidReminderSettings?: (args: { message: string; field: string }) => void;
  onRequestFailed?: (error: Error) => void;
}

const mocks = vi.hoisted(() => ({
  settingsData: undefined as unknown,
  saveReminderSettings: vi.fn(),
}));

vi.mock("../../../../api/queries/GetSettings/useGetSettings", () => ({
  default: () => ({ triggerAPI: vi.fn(), data: mocks.settingsData, apiStatus: 200, apiError: null }),
}));
vi.mock("../../../../api/mutations/UpdateTimezone/useUpdateTimezone", () => ({
  default: () => ({ triggerAPI: vi.fn(), apiStatus: API_INITIAL, apiError: null }),
}));
vi.mock("../../../../api/mutations/UpdateReminderSettings/useUpdateReminderSettings", () => ({
  default: () => ({ triggerAPI: mocks.saveReminderSettings, apiStatus: API_SUCCESS, apiError: null }),
}));

const loadedSettings = {
  settings: {
    timezone: "Asia/Kolkata",
    updatedAt: "2026-09-23T00:00:00Z",
    defaultReminderTime: "09:00",
    popupsEnabled: true,
    emailEnabled: true,
  },
};

const renderSettings = (): RootStore => {
  const store = new RootStore();
  store.auth.setMe({ id: "u1", email: "you@example.com", username: null, avatarUrl: null });
  render(
    <MemoryRouter>
      <StoreProvider store={store}>
        <SettingsController />
      </StoreProvider>
    </MemoryRouter>,
  );
  return store;
};

const lastSave = (): SaveArgs => mocks.saveReminderSettings.mock.lastCall?.[0] as SaveArgs;

describe("SettingsController, reminders", () => {
  beforeEach(() => {
    mocks.settingsData = loadedSettings;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("TC-3.10: skeleton rows until settings load", () => {
    mocks.settingsData = undefined;
    renderSettings();

    expect(screen.getByTestId("reminder-settings-loading")).toBeInTheDocument();
    expect(screen.queryByRole("switch", { name: "Email" })).not.toBeInTheDocument();
  });

  it("TC-3.10: loaded, it shows the time, both switches and the account email", () => {
    renderSettings();

    expect(screen.getByRole("combobox", { name: "Default reminder time" })).toHaveValue("09:00");
    expect(screen.getByRole("switch", { name: "Pop-ups in the app" })).toHaveAttribute(
      "aria-checked",
      "true",
    );
    expect(screen.getByRole("switch", { name: "Email" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByText("you@example.com")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Every reminder also lands in your notification list, whatever these switches say.",
      ),
    ).toBeInTheDocument();
  });

  it("TC-3.10: a change saves only that setting, with a spinner beside the control", () => {
    renderSettings();

    fireEvent.click(screen.getByRole("switch", { name: "Email" }));

    expect(lastSave().input).toEqual({ emailEnabled: false });
    const emailSwitch = screen.getByRole("switch", { name: "Email" });
    expect(emailSwitch).toHaveAttribute("aria-checked", "false");
    expect(emailSwitch).toBeDisabled();
    const row = emailSwitch.parentElement as HTMLElement;
    expect(within(row).getByRole("status", { name: "Saving" })).toBeInTheDocument();
  });

  it("TC-3.10: a failed save flips the switch back and says so", () => {
    renderSettings();

    fireEvent.click(screen.getByRole("switch", { name: "Email" }));
    act(() => lastSave().onRequestFailed?.(new Error("network")));

    expect(screen.getByRole("switch", { name: "Email" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn't turn email off. It is still on. Try again.",
    );
  });

  it("TC-3.10: turning both off shows the warning the server asks for, once", () => {
    const store = renderSettings();
    act(() => store.settings.setSettings({ timezone: "Asia/Kolkata", popupsEnabled: false }));

    fireEvent.click(screen.getByRole("switch", { name: "Email" }));
    act(() =>
      lastSave().onReminderSettingsSaved?.({
        settings: {
          timezone: "Asia/Kolkata",
          defaultReminderTime: "09:00",
          popupsEnabled: false,
          emailEnabled: false,
        },
        showBothOffWarning: true,
      }),
    );

    expect(screen.getByText("Nothing will reach you outside Slashit.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("switch", { name: "Pop-ups in the app" }));
    act(() =>
      lastSave().onReminderSettingsSaved?.({
        settings: {
          timezone: "Asia/Kolkata",
          defaultReminderTime: "09:00",
          popupsEnabled: true,
          emailEnabled: false,
        },
        showBothOffWarning: false,
      }),
    );

    expect(screen.queryByText("Nothing will reach you outside Slashit.")).not.toBeInTheDocument();
  });

  it("TC-3.10: a new default time saves and stays after the save", () => {
    const store = renderSettings();

    fireEvent.change(screen.getByRole("combobox", { name: "Default reminder time" }), {
      target: { value: "18:30" },
    });
    expect(lastSave().input).toEqual({ defaultReminderTime: "18:30" });
    act(() =>
      lastSave().onReminderSettingsSaved?.({
        settings: {
          timezone: "Asia/Kolkata",
          defaultReminderTime: "18:30",
          popupsEnabled: true,
          emailEnabled: true,
        },
        showBothOffWarning: false,
      }),
    );

    expect(store.settings.defaultReminderTime).toBe("18:30");
    expect(screen.getByRole("combobox", { name: "Default reminder time" })).toHaveValue("18:30");
  });

  it("TC-3.10: a refused time is put back, with the server's message on the field", () => {
    renderSettings();

    fireEvent.change(screen.getByRole("combobox", { name: "Default reminder time" }), {
      target: { value: "18:30" },
    });
    act(() =>
      lastSave().onInvalidReminderSettings?.({
        message: "Pick a time.",
        field: "defaultReminderTime",
      }),
    );

    expect(screen.getByRole("combobox", { name: "Default reminder time" })).toHaveValue("09:00");
    expect(screen.getByRole("alert")).toHaveTextContent("Pick a time.");
  });

  it("TC-4.11: the timezone note says what a change does to reminders", () => {
    renderSettings();

    expect(
      screen.getByText(
        /Repeating reminders keep their clock time in the new timezone\. One-time reminders keep their moment\./,
      ),
    ).toBeInTheDocument();
  });
});
