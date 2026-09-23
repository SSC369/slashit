import { CombinedGraphQLErrors } from "@apollo/client/errors";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { API_FAILED, API_INITIAL, API_SUCCESS } from "../../../../constants/apiConstants";
import type { ReminderFieldsFragment } from "../../../../fragments/ReminderFields.generated";
import { buildReminder as reminder } from "../../../../testing/reminderFixture";
import { StoreProvider } from "../../../../stores/StoreProvider";
import RecordsController from "./RecordsController";

const { mockUseGetRecords, mockUseRecordsViewOpened, mockUseGetReminders, mockUseOnlineStatus } =
  vi.hoisted(() => ({
    mockUseGetRecords: vi.fn(),
    mockUseRecordsViewOpened: vi.fn(),
    mockUseGetReminders: vi.fn(),
    mockUseOnlineStatus: vi.fn(),
  }));

vi.mock("../../../../api/queries/GetReminders/useGetReminders", () => ({
  default: () => mockUseGetReminders(),
}));

vi.mock("../../../../hooks/useOnlineStatus", () => ({
  useOnlineStatus: () => mockUseOnlineStatus(),
}));

vi.mock("../../../../api/queries/GetRecords/useGetRecords", () => ({
  default: () => mockUseGetRecords(),
}));

vi.mock("../../../../api/mutations/RecordsViewOpened/useRecordsViewOpened", () => ({
  default: () => mockUseRecordsViewOpened(),
}));

const renderWithProviders = () =>
  render(
    <MemoryRouter>
      <StoreProvider>
        <RecordsController />
      </StoreProvider>
    </MemoryRouter>,
  );

describe("RecordsController", () => {
  beforeEach(() => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockUseGetReminders.mockReturnValue({
      triggerAPI: vi.fn(),
      data: undefined,
      apiStatus: API_INITIAL,
      apiError: null,
    });
    mockUseRecordsViewOpened.mockReturnValue({
      triggerAPI: vi.fn(),
      apiStatus: API_INITIAL,
      apiError: null,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the empty state once a load has completed with zero records", () => {
    mockUseGetRecords.mockReturnValue({
      triggerAPI: vi.fn(),
      data: { records: [] },
      apiStatus: API_SUCCESS,
      apiError: null,
    });

    renderWithProviders();

    expect(screen.getByText("Nothing recorded yet")).toBeInTheDocument();
  });

  it("does not render the empty state before the first load completes", () => {
    mockUseGetRecords.mockReturnValue({
      triggerAPI: vi.fn(),
      data: undefined,
      apiStatus: API_INITIAL,
      apiError: null,
    });

    renderWithProviders();

    expect(screen.queryByText("Nothing recorded yet")).not.toBeInTheDocument();
  });

  it("renders the table, not the empty state, once records are loaded", () => {
    mockUseGetRecords.mockReturnValue({
      triggerAPI: vi.fn(),
      data: {
        records: [
          {
            __typename: "Task",
            id: "1",
            title: "Finish API docs",
            dueAt: null,
            status: "pending",
            isOverdue: false,
            origin: "command",
            originalInput: null,
            createdAt: "2026-09-13T00:00:00Z",
            updatedAt: "2026-09-13T00:00:00Z",
          },
        ],
      },
      apiStatus: API_SUCCESS,
      apiError: null,
    });

    renderWithProviders();

    expect(screen.queryByText("Nothing recorded yet")).not.toBeInTheDocument();
    expect(screen.getByText("Finish API docs")).toBeInTheDocument();
  });

  it("marks a reminder in the All tab with its own type and status", () => {
    mockUseGetRecords.mockReturnValue({
      triggerAPI: vi.fn(),
      data: { records: [{ __typename: "Reminder", ...reminder({ description: "Call Mom" }) }] },
      apiStatus: API_SUCCESS,
      apiError: null,
    });

    renderWithProviders();

    expect(screen.getByText("Call Mom")).toBeInTheDocument();
    expect(screen.getByText("Reminder")).toBeInTheDocument();
    expect(screen.getByText("Reminders carry a round marker, tasks a square one")).toBeInTheDocument();
  });

  describe("Reminders tab", () => {
    const openRemindersTab = (): void => {
      mockUseGetRecords.mockReturnValue({
        triggerAPI: vi.fn(),
        data: undefined,
        apiStatus: API_INITIAL,
        apiError: null,
      });
      renderWithProviders();
      fireEvent.click(screen.getByRole("button", { name: "Reminders" }));
    };

    const groups = (overrides: Partial<Record<"needsAttention" | "upcoming" | "done", ReminderFieldsFragment[]>>) => ({
      reminders: { needsAttention: [], upcoming: [], done: [], ...overrides },
    });

    it("shows skeleton rows under the real group headers while loading", () => {
      openRemindersTab();
      expect(screen.getByText("Needs attention")).toBeInTheDocument();
      expect(screen.getByText("Upcoming")).toBeInTheDocument();
      expect(screen.queryByText("No reminders yet")).not.toBeInTheDocument();
    });

    it("groups the loaded reminders and counts them against the cap", () => {
      mockUseGetReminders.mockReturnValue({
        triggerAPI: vi.fn(),
        data: groups({ upcoming: [reminder({ id: "r1", description: "Call Mom" })] }),
        apiStatus: API_SUCCESS,
        apiError: null,
      });
      openRemindersTab();
      expect(screen.getByText("Call Mom")).toBeInTheDocument();
      expect(screen.queryByText("Needs attention")).not.toBeInTheDocument();
      expect(screen.getByText("1 reminder · 1 active of 100")).toBeInTheDocument();
    });

    it("shows the empty state with the /remind example", () => {
      mockUseGetReminders.mockReturnValue({
        triggerAPI: vi.fn(),
        data: groups({}),
        apiStatus: API_SUCCESS,
        apiError: null,
      });
      openRemindersTab();
      expect(screen.getByText("No reminders yet")).toBeInTheDocument();
      expect(screen.getByText("/remind Call Mom tomorrow at 7pm")).toBeInTheDocument();
    });

    it("says the load failed and offers to try again", () => {
      const triggerAPI = vi.fn();
      mockUseGetReminders.mockReturnValue({
        triggerAPI,
        data: undefined,
        apiStatus: API_FAILED,
        apiError: new Error("Failed to fetch"),
      });
      openRemindersTab();
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      expect(screen.getByText("Couldn't load your reminders")).toBeInTheDocument();
      expect(triggerAPI).toHaveBeenCalledWith({ search: null });
    });

    it("shows the session card when the session has ended", () => {
      mockUseGetReminders.mockReturnValue({
        triggerAPI: vi.fn(),
        data: undefined,
        apiStatus: API_FAILED,
        apiError: new CombinedGraphQLErrors({ errors: [{ message: "Not authenticated" }] }),
      });
      openRemindersTab();
      expect(screen.getByText("Your session ended")).toBeInTheDocument();
    });

    it("names the search that matched nothing", () => {
      mockUseGetReminders.mockReturnValue({
        triggerAPI: vi.fn(),
        data: groups({}),
        apiStatus: API_SUCCESS,
        apiError: null,
      });
      openRemindersTab();
      fireEvent.change(screen.getByPlaceholderText("Search records"), { target: { value: "dentist" } });
      expect(screen.getByText("No reminders match “dentist”")).toBeInTheDocument();
    });

    it("keeps the saved list when offline and says so", () => {
      mockUseOnlineStatus.mockReturnValue(false);
      mockUseGetReminders.mockReturnValue({
        triggerAPI: vi.fn(),
        data: groups({ upcoming: [reminder({ id: "r1", description: "Call Mom" })] }),
        apiStatus: API_FAILED,
        apiError: new Error("Failed to fetch"),
      });
      openRemindersTab();
      expect(screen.getByText("Call Mom")).toBeInTheDocument();
      expect(screen.getByText("You are offline.")).toBeInTheDocument();
      expect(screen.getByText(/Showing what was saved on this device at/)).toBeInTheDocument();
    });
  });
});

