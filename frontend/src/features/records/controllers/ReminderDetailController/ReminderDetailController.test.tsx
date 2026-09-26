import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { API_INITIAL, API_SUCCESS } from "../../../../constants/apiConstants";
import type { ReminderFieldsFragment } from "../../../../fragments/ReminderFields.generated";
import { RootStore } from "../../../../stores/RootStore";
import { StoreProvider } from "../../../../stores/StoreProvider";
import { buildReminder } from "../../../../testing/reminderFixture";
import ReminderDetailController from "./ReminderDetailController";

const { mockUseGetReminder, mockUpdate, mockDelete, mockMarkDone, mockSnooze, mockUseOnlineStatus } =
  vi.hoisted(() => ({
    mockUseGetReminder: vi.fn(),
    mockUpdate: vi.fn(),
    mockDelete: vi.fn(),
    mockMarkDone: vi.fn(),
    mockSnooze: vi.fn(),
    mockUseOnlineStatus: vi.fn(),
  }));

vi.mock("../../../../api/queries/GetReminder/useGetReminder", () => ({
  default: () => mockUseGetReminder(),
}));
vi.mock("../../../../api/mutations/UpdateReminder/useUpdateReminder", () => ({
  default: () => ({ triggerAPI: mockUpdate, apiStatus: API_INITIAL, apiError: null }),
}));
vi.mock("../../../../api/mutations/DeleteReminder/useDeleteReminder", () => ({
  default: () => ({ triggerAPI: mockDelete, apiStatus: API_INITIAL, apiError: null }),
}));
vi.mock("../../../../api/mutations/MarkReminderDone/useMarkReminderDone", () => ({
  default: () => ({ triggerAPI: mockMarkDone, apiStatus: API_INITIAL, apiError: null }),
}));
vi.mock("../../../../api/mutations/SnoozeReminder/useSnoozeReminder", () => ({
  default: () => ({ triggerAPI: mockSnooze, apiStatus: API_INITIAL, apiError: null }),
}));
vi.mock("../../../../hooks/useOnlineStatus", () => ({
  useOnlineStatus: () => mockUseOnlineStatus(),
}));

const standup: ReminderFieldsFragment = buildReminder({
  id: "r1",
  description: "Standup notes",
  repeatKind: "WEEKLY",
  repeatWeekdays: [0, 1, 2, 3, 4],
  repeatText: "Every weekday",
  whenText: "Tomorrow, 9:30 AM",
  nextFireAt: "2026-09-24T04:00:00Z",
  localTime: "09:30",
});

const loadedAs = (reminder: ReminderFieldsFragment | null): void => {
  mockUseGetReminder.mockReturnValue({
    triggerAPI: vi.fn(),
    data:
      reminder === null
        ? { reminder: { __typename: "ReminderNotFound", message: "gone" } }
        : { reminder: { __typename: "Reminder", ...reminder } },
    apiStatus: API_SUCCESS,
    apiError: null,
  });
};

const renderAt = (path: string): RootStore => {
  const store = new RootStore();
  render(
    <MemoryRouter initialEntries={[path]}>
      <StoreProvider store={store}>
        <Routes>
          <Route path="/records/reminders/:id" element={<ReminderDetailController mode="VIEW" />} />
          <Route path="/records/reminders/:id/edit" element={<ReminderDetailController mode="EDIT" />} />
          <Route path="/records" element={<div>Records page</div>} />
        </Routes>
      </StoreProvider>
    </MemoryRouter>,
  );
  return store;
};

describe("ReminderDetailController", () => {
  beforeEach(() => {
    mockUseOnlineStatus.mockReturnValue(true);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("shows every field of the reminder", () => {
    loadedAs(standup);
    renderAt("/records/reminders/r1");

    expect(screen.getByText("Standup notes")).toBeInTheDocument();
    expect(screen.getByText("Mon to Fri, every week")).toBeInTheDocument();
    expect(screen.getByText("Asia/Kolkata")).toBeInTheDocument();
    expect(screen.getAllByText("Not yet")).toHaveLength(2);
  });

  it("shows Done and Snooze for a reminder that needs attention, and Done marks it done", () => {
    const fired = buildReminder({ id: "r1", description: "Standup notes", state: "FIRED" });
    loadedAs(fired);
    mockMarkDone.mockImplementation((args) => args.onReminderActed({ ...fired, state: "DONE" }));
    renderAt("/records/reminders/r1");

    expect(screen.getAllByText("Needs action")).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: /Done/ }));

    expect(mockMarkDone).toHaveBeenCalledWith(expect.objectContaining({ id: "r1" }));
    expect(screen.queryByRole("button", { name: /Done/ })).not.toBeInTheDocument();
  });

  it("does not show Done or Snooze once a reminder is done", () => {
    loadedAs(buildReminder({ id: "r1", state: "DONE" }));
    renderAt("/records/reminders/r1");

    expect(screen.queryByRole("button", { name: /Done/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Snooze/ })).not.toBeInTheDocument();
  });

  it("shows the skeleton until the reminder arrives", () => {
    mockUseGetReminder.mockReturnValue({ triggerAPI: vi.fn(), data: undefined, apiStatus: 100, apiError: null });
    renderAt("/records/reminders/r1");

    expect(screen.getByLabelText("Loading reminder")).toBeInTheDocument();
  });

  it("says not found for a missing or another user's id", () => {
    loadedAs(null);
    renderAt("/records/reminders/nope");

    expect(screen.getByText("This reminder doesn't exist or was deleted")).toBeInTheDocument();
  });

  it("disables Save and names the field while the draft is invalid", () => {
    loadedAs(standup);
    renderAt("/records/reminders/r1/edit");

    fireEvent.change(screen.getByLabelText("Reminder"), { target: { value: "" } });

    expect(screen.getByText("Give the reminder a name.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });

  it("shows the passed-time error under Time", () => {
    loadedAs(standup);
    mockUpdate.mockImplementation((args) =>
      args.onReminderTimePassed("That time has already passed. Pick a later time."),
    );
    renderAt("/records/reminders/r1/edit");

    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(screen.getByText("That time has already passed. Pick a later time.")).toBeInTheDocument();
  });

  it("keeps the edits and offers Try again when the save fails", () => {
    loadedAs(standup);
    mockUpdate.mockImplementation((args) => args.onRequestFailed(new Error("network")));
    renderAt("/records/reminders/r1/edit");

    fireEvent.change(screen.getByLabelText("Reminder"), { target: { value: "Standup" } });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(screen.getByText("Couldn't save your changes")).toBeInTheDocument();
    expect(screen.getByLabelText("Reminder")).toHaveValue("Standup");
    expect(screen.getByRole("button", { name: "Try again" })).toBeEnabled();
  });

  it("locks the form when the reminder was deleted elsewhere", () => {
    loadedAs(standup);
    mockUpdate.mockImplementation((args) => args.onReminderDeleted("deleted"));
    renderAt("/records/reminders/r1/edit");

    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(screen.getByText("This reminder was deleted")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Back to reminders" })).toBeInTheDocument();
  });

  it("sends the series and shows the success toast", () => {
    loadedAs(standup);
    mockUpdate.mockImplementation((args) => args.onReminderUpdated({ ...standup, localTime: "09:00" }));
    const store = renderAt("/records/reminders/r1/edit");

    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({ id: "r1", repeatKind: "WEEKLY", repeatWeekdays: [0, 1, 2, 3, 4] }),
    );
    expect(store.toast.current?.message).toBe("Reminder updated. Next: Thu 24 Sep, 9:30 AM");
  });

  it("names the whole series in the delete dialog and shows a failed delete inside it", () => {
    loadedAs(standup);
    mockDelete.mockImplementation((args) => args.onRequestFailed(new Error("network")));
    renderAt("/records/reminders/r1");

    fireEvent.click(screen.getByRole("button", { name: /Delete/ }));
    expect(
      screen.getByText(
        "“Standup notes” repeats every weekday. Deleting it removes the whole series, and it will not fire again.",
      ),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Delete reminder" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Couldn't delete it. The reminder is unchanged.");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("removes the reminder from the store and leaves after a delete", () => {
    loadedAs(standup);
    mockDelete.mockImplementation((args) => args.onReminderDeleted("r1"));
    const store = renderAt("/records/reminders/r1");

    fireEvent.click(screen.getByRole("button", { name: /Delete/ }));
    fireEvent.click(screen.getByRole("button", { name: "Delete reminder" }));

    expect(store.reminders.get("r1")).toBeNull();
    expect(screen.getByText("Records page")).toBeInTheDocument();
  });

  it("disables Edit and Delete while offline", () => {
    mockUseOnlineStatus.mockReturnValue(false);
    loadedAs(standup);
    renderAt("/records/reminders/r1");

    expect(screen.getByRole("button", { name: /Edit/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Delete/ })).toBeDisabled();
  });
});
