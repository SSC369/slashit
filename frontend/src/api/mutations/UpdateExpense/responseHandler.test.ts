import { describe, expect, it, vi } from "vitest";

import { buildExpense } from "../../../testing/expenseFixture";
import type { UpdateExpenseMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("UpdateExpense responseHandler", () => {
  it("hands the saved expense to onExpenseUpdated", () => {
    const { handleResponse } = useResponseHandler();
    const onExpenseUpdated = vi.fn();
    const expense = { __typename: "Expense" as const, ...buildExpense() };

    handleResponse({ data: { updateExpense: expense }, onExpenseUpdated });

    expect(onExpenseUpdated).toHaveBeenCalledWith(expense);
  });

  it("calls onExpenseInvalid with the field, reason and length", () => {
    const { handleResponse } = useResponseHandler();
    const onExpenseInvalid = vi.fn();
    const data: UpdateExpenseMutation = {
      updateExpense: {
        __typename: "ExpenseInvalid",
        message: "too long",
        field: "DESCRIPTION",
        reason: "TOO_LONG",
        length: 201,
      },
    };

    handleResponse({ data, onExpenseInvalid });

    expect(onExpenseInvalid).toHaveBeenCalledWith({
      message: "too long",
      field: "DESCRIPTION",
      reason: "TOO_LONG",
      length: 201,
    });
  });

  it("calls onExpenseNotFound with the message", () => {
    const { handleResponse } = useResponseHandler();
    const onExpenseNotFound = vi.fn();

    handleResponse({
      data: { updateExpense: { __typename: "ExpenseNotFound", message: "gone" } },
      onExpenseNotFound,
    });

    expect(onExpenseNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { updateExpense: { __typename: "Unknown" } } as unknown as UpdateExpenseMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled UpdateExpenseResult type");
  });
});
