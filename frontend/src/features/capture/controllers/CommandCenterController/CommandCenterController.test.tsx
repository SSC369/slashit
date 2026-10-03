import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RootStore } from "@/stores/RootStore";
import { StoreProvider } from "@/stores/StoreProvider";
import { buildExpense, buildExpenseSummary } from "@/testing/expenseFixture";
import { buildMemory } from "@/testing/memoryFixture";
import { buildReminder } from "@/testing/reminderFixture";
import { buildAnsweredResults } from "@/testing/searchFixture";
import CommandCenterController from "./CommandCenterController";

const {
  mockUseOnlineStatus,
  mockTriggerSubmitCapture,
  mockTriggerResolveMemoryConflict,
  mockTriggerRecordSearchEvent,
} = vi.hoisted(() => ({
  mockTriggerRecordSearchEvent: vi.fn(),
  mockUseOnlineStatus: vi.fn(),
  mockTriggerSubmitCapture: vi.fn(),
  mockTriggerResolveMemoryConflict: vi.fn(),
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

vi.mock("@/api/mutations/ResolveMemoryConflict/useResolveMemoryConflict", () => ({
  default: () => ({ triggerAPI: mockTriggerResolveMemoryConflict, apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/mutations/RecordSearchEvent/useRecordSearchEvent", () => ({
  default: () => ({ triggerAPI: mockTriggerRecordSearchEvent, apiStatus: 0, apiError: null }),
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

describe("CommandCenterController without /forget, F-5.1 of sub-plan 4.5", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("lists memory commands in the empty state but no /forget", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    renderWithProviders();

    expect(screen.getByText("/memories")).toBeInTheDocument();
    expect(screen.queryByText("/forget")).not.toBeInTheDocument();
  });
});

describe("CommandCenterController conflicts, F-3.2 of sub-plan 4.3", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  const runCommand = (command: string): void => {
    const input = screen.getByPlaceholderText("Type / to begin");
    fireEvent.change(input, { target: { value: command } });
    fireEvent.keyDown(input, { key: "Enter" });
  };

  const emirates = buildMemory({ id: "m1", text: "Preferred airline is Emirates" });
  const askConflict = (args: { onMemoryConflictAsked: (value: unknown) => void }) =>
    args.onMemoryConflictAsked({
      pendingCaptureId: "p1",
      newText: "My preferred airline is Qatar Airways",
      category: "PERSONAL",
      conflicting: [emirates],
    });

  it("Keep the new one saves it and drops the old memory from the store", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation(askConflict);
    const qatar = buildMemory({ id: "m9", text: "My preferred airline is Qatar Airways" });
    mockTriggerResolveMemoryConflict.mockImplementation((args) =>
      args.onMemorySaved({ memory: qatar, secretCaution: null }),
    );
    const store = new RootStore();
    store.memories.setMemories([emirates]);
    renderWithProviders(store);

    runCommand("/remember My preferred airline is Qatar Airways");
    expect(screen.getByText("1 question waiting")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Keep the new one" }));

    expect(mockTriggerResolveMemoryConflict).toHaveBeenCalledWith(
      expect.objectContaining({ pendingCaptureId: "p1", answer: "KEEP_NEW" }),
    );
    expect(screen.getByText("Memory saved · forgot 1 old memory")).toBeInTheDocument();
    expect(store.memories.get("m1")).toBeNull();
    expect(store.memories.get("m9")).not.toBeNull();
    expect(screen.queryByText("1 question waiting")).not.toBeInTheDocument();
  });

  it("Keep the old one and Both are correct resolve to their outcomes", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation(askConflict);
    mockTriggerResolveMemoryConflict
      .mockImplementationOnce((args) => args.onMemoryDiscarded("kept"))
      .mockImplementationOnce((args) =>
        args.onMemorySaved({ memory: buildMemory({ id: "m9" }), secretCaution: null }),
      );
    renderWithProviders();

    runCommand("/remember My preferred airline is Qatar Airways");
    fireEvent.click(screen.getByRole("radio", { name: "Keep the old one" }));
    fireEvent.click(screen.getByRole("button", { name: "Keep the old one" }));
    runCommand("/remember My preferred airline is Qatar Airways");
    fireEvent.click(screen.getByRole("radio", { name: "Both are correct" }));
    fireEvent.click(screen.getByRole("button", { name: "Both are correct" }));

    expect(screen.getByText("Kept your earlier memory")).toBeInTheDocument();
    expect(screen.getByText("Saved. Both memories kept")).toBeInTheDocument();
  });

  it("Decide later keeps the question waiting and sends nothing (FR-13)", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation(askConflict);
    renderWithProviders();

    runCommand("/remember My preferred airline is Qatar Airways");
    fireEvent.click(screen.getByRole("button", { name: "Decide later" }));

    expect(mockTriggerResolveMemoryConflict).not.toHaveBeenCalled();
    expect(screen.getByText("1 question waiting")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Answer now" })).toBeInTheDocument();
  });

  it("counts a 001 question and a deferred conflict together in the pill", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture
      .mockImplementationOnce((args) =>
        args.onPendingQuestionCreated({
          pendingCaptureId: "q1",
          question: "When should Slashit remind you?",
        }),
      )
      .mockImplementationOnce(askConflict);
    renderWithProviders();

    runCommand("/remind call mom");
    expect(screen.getByText("1 question waiting")).toBeInTheDocument();
    runCommand("/remember My preferred airline is Qatar Airways");
    fireEvent.click(screen.getByRole("button", { name: "Decide later" }));

    expect(screen.getByText("2 questions waiting")).toBeInTheDocument();
    mockTriggerSubmitCapture.mockReset();
  });

  it("reads the old memories live: one forgotten in Records drops out of the card", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation(askConflict);
    const store = new RootStore();
    renderWithProviders(store);

    runCommand("/remember My preferred airline is Qatar Airways");
    expect(screen.getByLabelText("Saved before")).toHaveTextContent("Preferred airline is Emirates");
    act(() => store.memories.removeMany(["m1"]));

    expect(screen.queryByLabelText("Saved before")).not.toBeInTheDocument();
    expect(screen.getByText(/has since been forgotten/)).toBeInTheDocument();
  });
});

/** Epic 005, sub-plan 4.2, C-2.15: opens are recorded with their position (PRD §8). */
describe("CommandCenterController search events", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  const askPassportQuestion = (): void => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation((args) => args.onSearchResults(buildAnsweredResults()));
    renderWithProviders();
    const input = screen.getByPlaceholderText("Type / to begin");
    fireEvent.change(input, { target: { value: "/search when does my passport expire?" } });
    fireEvent.keyDown(input, { key: "Enter" });
  };

  it("records a followed citation with its number", () => {
    askPassportQuestion();

    fireEvent.click(screen.getByRole("button", { name: "source 2: Renew passport" }));

    expect(mockTriggerRecordSearchEvent).toHaveBeenCalledWith({
      kind: "ANSWER_CITATION_OPENED",
      position: 2,
    });
  });

  it("records an opened row with its place down the card", () => {
    askPassportQuestion();

    fireEvent.click(screen.getByText("Renew passport"));

    expect(mockTriggerRecordSearchEvent).toHaveBeenCalledWith({
      kind: "SEARCH_RESULT_OPENED",
      position: 2,
    });
  });
});

describe("CommandCenterController /add-expense", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  const runCommand = (command: string): void => {
    const input = screen.getByPlaceholderText("Type / to begin");
    fireEvent.change(input, { target: { value: command } });
    fireEvent.keyDown(input, { key: "Enter" });
  };

  it("shows the saved card and holds the expense in its store", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    const expense = buildExpense({ id: "e1" });
    mockTriggerSubmitCapture.mockImplementation((args) => args.onExpenseSaved(expense));
    const store = new RootStore();
    renderWithProviders(store);

    runCommand("/add-expense ₹850 dinner with friends yesterday");

    expect(screen.getByText("Expense saved")).toBeInTheDocument();
    expect(store.expenses.get("e1")).toEqual(expense);
  });

  it("reads a saved expense live, so an edit in Records shows on the card", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    const expense = buildExpense({ id: "e1" });
    mockTriggerSubmitCapture.mockImplementation((args) => args.onExpenseSaved(expense));
    const store = new RootStore();
    renderWithProviders(store);
    runCommand("/add-expense ₹850 dinner");

    act(() => store.expenses.upsert({ ...expense, description: "Team dinner" }));

    expect(screen.getByText("Team dinner")).toBeInTheDocument();
  });

  it("counts an expense question as waiting", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation((args) =>
      args.onExpenseQuestionAsked({
        pendingCaptureId: "pc-1",
        kind: "AMOUNT",
        question: "How much was it?",
        amountCandidates: [],
        readDate: null,
      }),
    );
    const store = new RootStore();
    renderWithProviders(store);

    runCommand("/add-expense dinner at Toit");

    expect(screen.getByText("How much was it?")).toBeInTheDocument();
    expect(store.capture.waitingCount).toBe(1);
  });

  it("refuses another currency and keeps the text in the box (FR-6)", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation((args) =>
      args.onExpenseRefused({ message: "rupees only", reason: "FOREIGN_CURRENCY", length: null }),
    );
    renderWithProviders();

    runCommand("/add-expense $20 lunch in Singapore");

    expect(screen.getByRole("alert")).toHaveTextContent("Slashit records rupees only for now.");
    expect(screen.getByPlaceholderText("Type / to begin")).toHaveValue("/add-expense $20 lunch in Singapore");
  });

  it("keeps the text in the box when the model is down (FR-14)", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation((args) => args.onProviderUnavailable("down"));
    renderWithProviders();

    runCommand("/add-expense ₹640 pharmacy");

    expect(screen.getByRole("alert")).toHaveTextContent("Slashit could not save this right now.");
    expect(screen.getByPlaceholderText("Type / to begin")).toHaveValue("/add-expense ₹640 pharmacy");
  });

  it("shows the summary card, and Open in Records picks its period on the Expenses tab (F-10)", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    const summary = buildExpenseSummary();
    mockTriggerSubmitCapture.mockImplementation((args) => args.onExpenseSummary(summary));
    const store = new RootStore();
    renderWithProviders(store);

    runCommand("/expenses last month");
    fireEvent.click(screen.getByRole("button", { name: /Open in Records/ }));

    expect(store.records.kindFilter).toBe("EXPENSES");
    expect(store.expenses.periodId).toBe("2026-09-01|2026-09-30");
  });

  it("refuses a period it cannot read, quoting it and keeping the text (FR-27)", () => {
    mockUseOnlineStatus.mockReturnValue(true);
    mockTriggerSubmitCapture.mockImplementation((args) =>
      args.onExpenseRefused({ message: "not understood", reason: "PERIOD_NOT_UNDERSTOOD", length: null }),
    );
    renderWithProviders();

    runCommand("/expenses since diwali");

    expect(screen.getByRole("alert")).toHaveTextContent("Slashit did not understand “since diwali”.");
    expect(screen.getByPlaceholderText("Type / to begin")).toHaveValue("/expenses since diwali");
  });
});
