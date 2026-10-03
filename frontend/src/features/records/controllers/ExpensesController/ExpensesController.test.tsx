import { CombinedGraphQLErrors } from "@apollo/client/errors";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { ExpensePeriodFragment } from "../../../../api/queries/GetExpensePeriods/responseHandler";
import { API_FAILED, API_FETCHING, API_SUCCESS } from "../../../../constants/apiConstants";
import type { ExpenseSummaryFieldsFragment } from "../../../../fragments/ExpenseSummaryFields.generated";
import { periodIdOf } from "../../../../stores/ExpensesStore";
import { RootStore } from "../../../../stores/RootStore";
import { StoreProvider } from "../../../../stores/StoreProvider";
import { buildExpense, buildExpenseSummary } from "../../../../testing/expenseFixture";
import ExpensesController from "./ExpensesController";

const { mockUseGetExpenses, mockUseGetExpensePeriods, mockUseGetExpenseSummary, mockIsOnline } =
  vi.hoisted(() => ({
    mockUseGetExpenses: vi.fn(),
    mockUseGetExpensePeriods: vi.fn(),
    mockUseGetExpenseSummary: vi.fn(),
    mockIsOnline: { current: true },
  }));

vi.mock("../../../../api/queries/GetExpenses/useGetExpenses", () => ({
  default: () => mockUseGetExpenses(),
}));

vi.mock("../../../../api/queries/GetExpensePeriods/useGetExpensePeriods", () => ({
  default: () => mockUseGetExpensePeriods(),
}));

vi.mock("../../../../api/queries/GetExpenseSummary/useGetExpenseSummary", () => ({
  default: () => mockUseGetExpenseSummary(),
}));

vi.mock("../../../../hooks/useOnlineStatus", () => ({ useOnlineStatus: () => mockIsOnline.current }));

const PERIODS: ExpensePeriodFragment[] = [
  { key: "THIS_MONTH", label: "October 2026 so far", phrase: "this month", start: "2026-10-01", end: "2026-10-31" },
  { key: "LAST_MONTH", label: "September 2026", phrase: "in September 2026", start: "2026-09-01", end: "2026-09-30" },
  { key: "ALL_TIME", label: "All time", phrase: "yet", start: null, end: null },
];

const withPeriods = () => ({
  triggerAPI: vi.fn(),
  data: { expensePeriods: PERIODS },
  apiStatus: API_SUCCESS,
  apiError: null,
});

const withSummary = (summary: ExpenseSummaryFieldsFragment | null) => ({
  triggerAPI: vi.fn(),
  data: summary === null ? undefined : { expenseSummary: summary },
  apiStatus: API_SUCCESS,
  apiError: null,
});

const withExpenses = (expenses: ReturnType<typeof buildExpense>[]) => ({
  triggerAPI: vi.fn(),
  data: { expenses: expenses.map((expense) => ({ __typename: "Expense" as const, ...expense })) },
  apiStatus: API_SUCCESS,
  apiError: null,
});

const renderTab = (store: RootStore = new RootStore()) =>
  render(
    <MemoryRouter>
      <StoreProvider store={store}>
        <ExpensesController />
      </StoreProvider>
    </MemoryRouter>,
  );

describe("ExpensesController, F-4 of 4.1 and F-8, F-9 of 4.2", () => {
  beforeEach(() => {
    mockUseGetExpensePeriods.mockReturnValue(withPeriods());
    mockUseGetExpenseSummary.mockReturnValue(withSummary(null));
  });

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

  it("opens on this month and asks for its range, list and band together (F-8, decision 1A)", () => {
    const list = withExpenses([buildExpense()]);
    const summary = withSummary(null);
    mockUseGetExpenses.mockReturnValue(list);
    mockUseGetExpenseSummary.mockReturnValue(summary);
    const store = new RootStore();

    renderTab(store);

    const thisMonth = { category: null, start: "2026-10-01", end: "2026-10-31" };
    expect(store.expenses.selectedPeriod?.key).toBe("THIS_MONTH");
    expect(list.triggerAPI).toHaveBeenLastCalledWith({ filter: thisMonth });
    expect(summary.triggerAPI).toHaveBeenLastCalledWith({ filter: thisMonth });
  });

  it("sends no range for All time (decision 2A)", () => {
    const list = withExpenses([buildExpense()]);
    mockUseGetExpenses.mockReturnValue(list);
    const store = new RootStore();
    store.expenses.selectPeriod(periodIdOf({ start: null, end: null }));

    renderTab(store);

    expect(list.triggerAPI).toHaveBeenLastCalledWith({ filter: { category: null, start: null, end: null } });
  });

  it("lists expenses under the band with total and category cells (FR-16, FR-18, F-9)", () => {
    mockUseGetExpenses.mockReturnValue(
      withExpenses([
        buildExpense(),
        buildExpense({ id: "e-2", description: "Uber to office", category: "TRANSPORT", amountPaise: "32000" }),
      ]),
    );
    mockUseGetExpenseSummary.mockReturnValue(withSummary(buildExpenseSummary()));
    const store = new RootStore();
    store.expenses.selectPeriod(periodIdOf({ start: "2026-09-01", end: "2026-09-30" }));

    renderTab(store);

    const table = within(screen.getByRole("table"));
    expect(table.getByText("Dinner with friends")).toBeInTheDocument();
    expect(table.getByText("₹320")).toBeInTheDocument();
    expect(screen.getByText("2 expenses · newest first")).toBeInTheDocument();
    const band = within(screen.getByRole("region", { name: "Spent, September 2026" }));
    expect(band.getByText("₹38,450")).toBeInTheDocument();
    expect(band.getByText("Food")).toBeInTheDocument();
    expect(band.getByText("₹8,650")).toBeInTheDocument();
  });

  it("filters by a category chip, for the same period", () => {
    const list = withExpenses([buildExpense()]);
    mockUseGetExpenses.mockReturnValue(list);
    renderTab();

    fireEvent.click(screen.getByRole("button", { name: "Food" }));

    expect(list.triggerAPI).toHaveBeenLastCalledWith({
      filter: { category: "FOOD", start: "2026-10-01", end: "2026-10-31" },
    });
    expect(screen.getByRole("button", { name: "Food" })).toHaveAttribute("aria-pressed", "true");
  });

  it("names an empty period and hides the band (FR-26, F-9)", () => {
    mockUseGetExpenses.mockReturnValue(withExpenses([]));

    renderTab();

    expect(screen.getByText("No expenses recorded this month")).toBeInTheDocument();
    expect(screen.queryByRole("region")).not.toBeInTheDocument();
  });

  it("asks for the all-time count when the picked period is empty (dev log E-6)", () => {
    mockUseGetExpenses.mockReturnValue(withExpenses([]));
    const summaryHook = withSummary(null);
    mockUseGetExpenseSummary.mockReturnValue(summaryHook);

    renderTab();

    expect(summaryHook.triggerAPI).toHaveBeenCalledWith({ filter: { category: null, start: null, end: null } });
  });

  it("greets a user with no expenses at all as new, on any period (dev log E-6)", () => {
    mockUseGetExpenses.mockReturnValue(withExpenses([]));
    mockUseGetExpenseSummary.mockReturnValue(
      withSummary(buildExpenseSummary({ count: 0, grandTotalPaise: "0", totals: [] })),
    );

    renderTab();

    expect(screen.getByText("No expenses yet")).toBeInTheDocument();
    expect(screen.queryByText("No expenses recorded this month")).not.toBeInTheDocument();
  });

  it("keeps the empty-period copy for a user who has expenses in other periods", () => {
    mockUseGetExpenses.mockReturnValue(withExpenses([]));
    mockUseGetExpenseSummary.mockReturnValue(withSummary(buildExpenseSummary({ count: 3 })));

    renderTab();

    expect(screen.getByText("No expenses recorded this month")).toBeInTheDocument();
  });

  it("draws the empty state with an example command on All time", () => {
    mockUseGetExpenses.mockReturnValue(withExpenses([]));
    const store = new RootStore();
    store.expenses.selectPeriod(periodIdOf({ start: null, end: null }));

    renderTab(store);

    expect(screen.getByText("No expenses yet")).toBeInTheDocument();
    expect(screen.getByText("/add-expense ₹850 dinner yesterday")).toBeInTheDocument();
  });

  it("names the category and period when a filter matches nothing, and clears back to All", () => {
    mockUseGetExpenses.mockReturnValue(withExpenses([buildExpense()]));
    renderTab();

    mockUseGetExpenses.mockReturnValue(withExpenses([]));
    fireEvent.click(screen.getByRole("button", { name: "Health" }));

    expect(screen.getByText("No Health expenses in October 2026 so far")).toBeInTheDocument();
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

  it("draws the error state when the periods cannot load", () => {
    mockUseGetExpensePeriods.mockReturnValue({ triggerAPI: vi.fn(), data: undefined, apiStatus: API_FAILED, apiError: new Error("network") });
    mockUseGetExpenses.mockReturnValue({ triggerAPI: vi.fn(), data: undefined, apiStatus: 0, apiError: null });

    renderTab();

    expect(screen.getByText("Your expenses could not be loaded")).toBeInTheDocument();
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

describe("ExpensesController band, stale totals", () => {
  it("hides totals that belong to another period", () => {
    mockUseGetExpensePeriods.mockReturnValue(withPeriods());
    mockUseGetExpenses.mockReturnValue(withExpenses([buildExpense()]));
    mockUseGetExpenseSummary.mockReturnValue(withSummary(buildExpenseSummary()));

    renderTab();

    expect(screen.queryByRole("region")).not.toBeInTheDocument();
  });
});
