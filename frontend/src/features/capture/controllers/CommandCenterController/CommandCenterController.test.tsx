import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RootStore } from "@/stores/RootStore";
import { StoreProvider } from "@/stores/StoreProvider";
import { buildReminder } from "@/testing/reminderFixture";
import CommandCenterController from "./CommandCenterController";

const { mockUseOnlineStatus, mockTriggerSubmitCapture } = vi.hoisted(() => ({
  mockUseOnlineStatus: vi.fn(),
  mockTriggerSubmitCapture: vi.fn(),
}));

vi.mock("@/hooks/useOnlineStatus", () => ({
  useOnlineStatus: () => mockUseOnlineStatus(),
}));

vi.mock("@/api/mutations/SubmitCapture/useSubmitCapture", () => ({
  default: () => ({ triggerAPI: mockTriggerSubmitCapture, apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/mutations/AnswerPendingCapture/useAnswerPendingCapture", () => ({
  default: () => ({ triggerAPI: vi.fn(), apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/mutations/DiscardPendingCapture/useDiscardPendingCapture", () => ({
  default: () => ({ triggerAPI: vi.fn(), apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/queries/GetCaptureHistory/useGetCaptureHistory", () => ({
  default: () => ({ triggerAPI: vi.fn(), data: undefined, apiStatus: 0, apiError: null }),
}));

const renderWithProviders = (store: RootStore = new RootStore()) =>
  render(
    <MemoryRouter>
      <StoreProvider store={store}>
        <CommandCenterController />
      </StoreProvider>
    </MemoryRouter>,
  );

describe("CommandCenterController offline behaviour", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("T-3.4: disables the input and shows the offline note while offline", () => {
    mockUseOnlineStatus.mockReturnValue(false);

    renderWithProviders();

    const input = screen.getByPlaceholderText("You're offline");
    expect(input).toBeDisabled();
  });

  it("T-3.4: never dispatches submitCapture while offline, even if Enter fires", () => {
    mockUseOnlineStatus.mockReturnValue(false);

    renderWithProviders();
    const input = screen.getByPlaceholderText("You're offline");
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));

    expect(mockTriggerSubmitCapture).not.toHaveBeenCalled();
  });

  it("enables the input again once back online", () => {
    mockUseOnlineStatus.mockReturnValue(true);

    renderWithProviders();

    const input = screen.getByPlaceholderText("Type / to begin");
    expect(input).not.toBeDisabled();
  });
});

describe("CommandCenterController /remind", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  const runCommand = (command: string): void => {
    const input = screen.getByPlaceholderText("Type / to begin");
    fireEvent.change(input, { target: { value: command } });
    fireEvent.keyDown(input, { key: "Enter" });
  };

  it("shows the reminder as understood, with the resolved-time note, and a success toast", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    const reminder = buildReminder({
      id: "r1",
      description: "Renew insurance",
      whenText: "Thu 15 Oct, 9:00 AM",
      whenNote: "No time given, so your default reminder time",
    });
    mockTriggerSubmitCapture.mockImplementation((args) => args.onReminderCreated(reminder));
    const store = new RootStore();
    renderWithProviders(store);

    runCommand("/remind Renew insurance Oct 15");

    expect(screen.getByText("Reminder set")).toBeInTheDocument();
    expect(screen.getByText("No time given, so your default reminder time")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Change default time" })).toHaveAttribute(
      "href",
      "/settings",
    );
    expect(store.toast.current?.message).toBe("Reminder set for Thu 15 Oct, 9:00 AM");
    expect(store.reminders.get("r1")).toEqual(reminder);
  });

  it("refuses at the cap and puts what was typed back in the bar", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation((args) =>
      args.onReminderLimitReached({ message: "cap", limit: 100 }),
    );
    renderWithProviders();

    runCommand("/remind Book car service next Friday");

    expect(screen.getByText("You have 100 active reminders, the most Slashit holds.")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Type / to begin")).toHaveValue(
      "/remind Book car service next Friday",
    );
  });

  it("says the model can't read it now, keeps the command, and saves nothing", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation((args) =>
      args.onProviderUnavailable("The model provider is unavailable"),
    );
    const store = new RootStore();
    renderWithProviders(store);

    runCommand("/remind Call Mom tomorrow at 7pm");

    expect(screen.getByText("Slashit can't read that right now")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Type / to begin")).toHaveValue("/remind Call Mom tomorrow at 7pm");
    expect(store.toast.current).toBeNull();
  });

  it("lists /reminders soonest first as the server sent them", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation((args) =>
      args.onRemindersListed([
        buildReminder({ id: "a", description: "Call Mom" }),
        buildReminder({ id: "b", description: "Water the plants" }),
      ]),
    );
    renderWithProviders();

    runCommand("/reminders ");

    expect(screen.getByText("2 active reminders · soonest first")).toBeInTheDocument();
    const names = screen.getAllByText(/Call Mom|Water the plants/).map((node) => node.textContent);
    expect(names).toEqual(["Call Mom", "Water the plants"]);
  });
});
