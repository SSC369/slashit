import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RootStore } from "@/stores/RootStore";
import { StoreProvider } from "@/stores/StoreProvider";
import { buildExpense } from "@/testing/expenseFixture";
import ExpenseDetailController from "./ExpenseDetailController";

const { mockTriggerDeleteExpense, mockTriggerUpdateExpense, mockTriggerRelated } = vi.hoisted(() => ({
  mockTriggerDeleteExpense: vi.fn(),
  mockTriggerUpdateExpense: vi.fn(),
  mockTriggerRelated: vi.fn(),
}));

vi.mock("@/hooks/useOnlineStatus", () => ({ useOnlineStatus: () => true }));

vi.mock("@/api/queries/GetExpense/useGetExpense", () => ({
  default: () => ({ triggerAPI: vi.fn(), data: undefined, apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/mutations/UpdateExpense/useUpdateExpense", () => ({
  default: () => ({ triggerAPI: mockTriggerUpdateExpense, apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/mutations/DeleteExpense/useDeleteExpense", () => ({
  default: () => ({ triggerAPI: mockTriggerDeleteExpense, apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/queries/GetRelatedRecords/useGetRelatedRecords", () => ({
  default: () => ({ triggerAPI: mockTriggerRelated, data: undefined, apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/mutations/RecordSearchEvent/useRecordSearchEvent", () => ({
  default: () => ({ triggerAPI: vi.fn(), apiStatus: 0, apiError: null }),
}));

const expense = buildExpense({ id: "e1" });

const renderDetail = (store: RootStore, path = "/records/expenses/e1") =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <StoreProvider store={store}>
        <Routes>
          <Route path="/records/expenses/:id" element={<ExpenseDetailController mode="VIEW" />} />
          <Route path="/records/expenses/:id/edit" element={<ExpenseDetailController mode="EDIT" />} />
          <Route path="/records" element={<div>Records page</div>} />
        </Routes>
      </StoreProvider>
    </MemoryRouter>,
  );

describe("ExpenseDetailController, F-5 of sub-plan 4.1", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("shows the amount as headline and every field (FR-20)", () => {
    const store = new RootStore();
    store.expenses.upsert(expense);
    renderDetail(store);

    expect(screen.getByLabelText("850 rupees")).toHaveTextContent("₹850");
    expect(screen.getByText("Thursday 1 October 2026")).toBeInTheDocument();
    expect(screen.getByText("Never")).toBeInTheDocument();
    expect(screen.getByText(expense.originalInput)).toBeInTheDocument();
  });

  it("names the amount and description in the delete dialog, then removes it everywhere (FR-22)", () => {
    const store = new RootStore();
    store.expenses.setExpenses([expense]);
    mockTriggerDeleteExpense.mockImplementation((args) => args.onExpenseDeleted("e1"));
    renderDetail(store);

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    const dialog = screen.getByRole("dialog", { name: "Delete this expense?" });
    expect(dialog).toHaveTextContent("₹850 · Dinner with friends will be removed from your records and from every total.");

    fireEvent.click(screen.getByRole("button", { name: "Delete expense" }));

    expect(store.expenses.get("e1")).toBeNull();
    expect(store.expenses.getVisible()).toEqual([]);
    expect(store.records.kindFilter).toBe("EXPENSES");
    expect(store.toast.current?.message).toBe("Expense deleted. It no longer counts in any total.");
    expect(screen.getByText("Records page")).toBeInTheDocument();
  });

  it("keeps the dialog open with the failure copy when the delete fails", () => {
    const store = new RootStore();
    store.expenses.upsert(expense);
    mockTriggerDeleteExpense.mockImplementation((args) => args.onRequestFailed(new Error("network")));
    renderDetail(store);

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete expense" }));

    expect(screen.getByRole("alert")).toHaveTextContent("This expense could not be deleted.");
    expect(store.expenses.get("e1")).not.toBeNull();
  });

  it("sends only the fields that changed", () => {
    const store = new RootStore();
    store.expenses.upsert(expense);
    renderDetail(store, "/records/expenses/e1/edit");

    fireEvent.change(screen.getByLabelText("Amount"), { target: { value: "1,200.50" } });
    fireEvent.click(screen.getByRole("radio", { name: "Entertainment" }));
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(mockTriggerUpdateExpense).toHaveBeenCalledWith(
      expect.objectContaining({ id: "e1", input: { amountPaise: "120050", category: "ENTERTAINMENT" } }),
    );
  });

  it("shows the server's field error from ExpenseInvalid", () => {
    const store = new RootStore();
    store.expenses.upsert(expense);
    mockTriggerUpdateExpense.mockImplementation((args) =>
      args.onExpenseInvalid({ message: "Enter a description.", field: "DESCRIPTION", reason: "EMPTY", length: null }),
    );
    renderDetail(store, "/records/expenses/e1/edit");

    fireEvent.change(screen.getByLabelText("Description"), { target: { value: "Team dinner" } });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(screen.getByText("Enter a description.")).toBeInTheDocument();
  });
});

describe("ExpenseDetailController related records, F-13 of sub-plan 4.3", () => {
  it("lists records close in meaning below the expense (005 FR-25)", () => {
    const store = new RootStore();
    store.expenses.upsert(expense);
    renderDetail(store);

    expect(screen.getByRole("region", { name: "Related records" })).toBeInTheDocument();
    expect(mockTriggerRelated).toHaveBeenCalledWith({ recordType: "EXPENSE", id: "e1" });
  });
});
