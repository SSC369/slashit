import { describe, expect, it, vi } from "vitest";

import { buildExpense } from "../../../testing/expenseFixture";
import type { GetExpenseQuery } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("GetExpense responseHandler", () => {
  it("hands a found expense to onExpenseLoaded", () => {
    const { handleResponse } = useResponseHandler();
    const onExpenseLoaded = vi.fn();
    const expense = { __typename: "Expense" as const, ...buildExpense() };

    handleResponse({ data: { expense }, onExpenseLoaded });

    expect(onExpenseLoaded).toHaveBeenCalledWith(expense);
  });

  it("calls onExpenseNotFound for ExpenseNotFound", () => {
    const { handleResponse } = useResponseHandler();
    const onExpenseNotFound = vi.fn();

    handleResponse({
      data: { expense: { __typename: "ExpenseNotFound", message: "gone" } },
      onExpenseNotFound,
    });

    expect(onExpenseNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { expense: { __typename: "Unknown" } } as unknown as GetExpenseQuery;

    expect(() => handleResponse({ data })).toThrow("Unhandled ExpenseResult type");
  });
});
