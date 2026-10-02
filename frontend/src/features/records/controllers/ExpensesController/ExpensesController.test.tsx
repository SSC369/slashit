import { CombinedGraphQLErrors } from "@apollo/client/errors";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { API_FAILED, API_FETCHING, API_SUCCESS } from "../../../../constants/apiConstants";
import { RootStore } from "../../../../stores/RootStore";
import { StoreProvider } from "../../../../stores/StoreProvider";
import { buildExpense } from "../../../../testing/expenseFixture";
import ExpensesController from "./ExpensesController";

const { mockUseGetExpenses, mockIsOnline } = vi.hoisted(() => ({
  mockUseGetExpenses: vi.fn(),
  mockIsOnline: { current: true },
}));

vi.mock("../../../../api/queries/GetExpenses/useGetExpenses", () => ({
  default: () => mockUseGetExpenses(),
}));

vi.mock("../../../../hooks/useOnlineStatus", () => ({ useOnlineStatus: () => mockIsOnline.current }));

const renderTab = (store: RootStore = new RootStore()) =>
  render(
    <MemoryRouter>
      <StoreProvider store={store}>
        <ExpensesController />
      </StoreProvider>
    </MemoryRouter>,
  );

const withExpenses = (expenses: ReturnType<typeof buildExpense>[]) => ({
  triggerAPI: vi.fn(),
  data: { expenses: expenses.map((expense) => ({ __typename: "Expense" as const, ...expense })) },
  apiStatus: API_SUCCESS,
  apiError: null,
});

describe("ExpensesController, F-4 of sub-plan 4.1", () => {
  afterEach(() => {
    vi.clearAllMocks();
    mockIsOnline.current = true;
  });

  it("draws the loading skeleton before the first load", () => {
    mockUseGetExpenses.mockReturnValue({ triggerAPI: vi.fn(), data: undefined, apiStatus: API_FETCHING, apiError: null });

    renderTab();

    expect(screen.getByRole("group", { name: "Filter by category" })).toBeInTheDocument();
    expect(screen.queryByText("Only you can see these")).not.toBeInTheDocument();
  });

  it("lists expenses with date, category and amount, and a count (FR-16)", () => {
    mockUseGetExpenses.mockReturnValue(
      withExpenses([
        buildExpense(),
        buildExpense({ id: "e-2", description: "Uber to office", category: "TRANSPORT", amountPaise: "32000" }),
      ]),
    );

    renderTab();

    const table = within(screen.getByRole("table"));
    expect(table.getByText("Dinner with friends")).toBeInTheDocument();
    expect(table.getAllByText("Thu 1 Oct")).toHaveLength(2);
    expect(table.getByText("Transport")).toBeInTheDocument();
    expect(table.getByText("₹320")).toBeInTheDocument();
    expect(screen.getByText("2 expenses · newest first")).toBeInTheDocument();
  });

  it("filters by a category chip and asks the server for it (FR-17)", () => {
    const loaded = withExpenses([buildExpense()]);
    mockUseGetExpenses.mockReturnValue(loaded);
    renderTab();

    fireEvent.click(screen.getByRole("button", { name: "Food" }));

    expect(loaded.triggerAPI).toHaveBeenLastCalledWith({ filter: { category: "FOOD" } });
    expect(screen.getByRole("button", { name: "Food" })).toHaveAttribute("aria-pressed", "true");
  });

  it("draws the empty state with an example command", () => {
    mockUseGetExpenses.mockReturnValue(withExpenses([]));

    renderTab();

    expect(screen.getByText("No expenses yet")).toBeInTheDocument();
    expect(screen.getByText("/add-expense ₹850 dinner yesterday")).toBeInTheDocument();
  });

  it("draws the filtered no-match state and clears back to All", () => {
    mockUseGetExpenses.mockReturnValue(withExpenses([buildExpense()]));
    renderTab();

    mockUseGetExpenses.mockReturnValue(withExpenses([]));
    fireEvent.click(screen.getByRole("button", { name: "Health" }));

    expect(screen.getByText("No Health expenses")).toBeInTheDocument();
    mockUseGetExpenses.mockReturnValue(withExpenses([buildExpense()]));
    fireEvent.click(screen.getByRole("button", { name: "Show all" }));
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
  });

  it("draws the error state with a retry", () => {
    const triggerAPI = vi.fn();
    mockUseGetExpenses.mockReturnValue({ triggerAPI, data: undefined, apiStatus: API_FAILED, apiError: new Error("network") });

    renderTab();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(screen.getByText("Your expenses could not be loaded")).toBeInTheDocument();
    expect(triggerAPI).toHaveBeenCalled();
  });

  it("draws the signed-out state when the session has ended", () => {
    mockUseGetExpenses.mockReturnValue({
      triggerAPI: vi.fn(),
      data: undefined,
      apiStatus: API_FAILED,
      apiError: new CombinedGraphQLErrors({ errors: [{ message: "Not authenticated" }] }),
    });

    renderTab();

    expect(screen.getByText("Sign in to see your expenses")).toBeInTheDocument();
  });

  it("keeps loaded rows readable offline, under the offline note", () => {
    mockIsOnline.current = false;
    const store = new RootStore();
    store.expenses.setExpenses([buildExpense()]);
    mockUseGetExpenses.mockReturnValue({ triggerAPI: vi.fn(), data: undefined, apiStatus: API_FAILED, apiError: new Error("offline") });

    renderTab(store);

    expect(screen.getByRole("status")).toHaveTextContent("You are offline.");
    expect(screen.getByText("Dinner with friends")).toBeInTheDocument();
  });
});
