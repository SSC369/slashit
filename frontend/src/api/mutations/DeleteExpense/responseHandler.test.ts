import { describe, expect, it, vi } from "vitest";

import type { DeleteExpenseMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("DeleteExpense responseHandler", () => {
  it("hands the id to onExpenseDeleted", () => {
    const { handleResponse } = useResponseHandler();
    const onExpenseDeleted = vi.fn();

    handleResponse({
      data: { deleteExpense: { __typename: "ExpenseDeleted", id: "expense-1" } },
      onExpenseDeleted,
    });

    expect(onExpenseDeleted).toHaveBeenCalledWith("expense-1");
  });

  it("calls onExpenseNotFound with the message", () => {
    const { handleResponse } = useResponseHandler();
    const onExpenseNotFound = vi.fn();

    handleResponse({
      data: { deleteExpense: { __typename: "ExpenseNotFound", message: "gone" } },
      onExpenseNotFound,
    });

    expect(onExpenseNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { deleteExpense: { __typename: "Unknown" } } as unknown as DeleteExpenseMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled DeleteExpenseResult type");
  });
});
