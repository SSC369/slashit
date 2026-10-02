import type { ExpenseField, ExpenseInvalidReason } from "../../../../types.generated";
import type { ExpenseFieldsFragment } from "../../../fragments/ExpenseFields.generated";
import type { UpdateExpenseMutation } from "./operation.generated";

export interface UpdateExpenseCallbacks {
  onExpenseUpdated?: (expense: ExpenseFieldsFragment) => void;
  onExpenseNotFound?: (message: string) => void;
  onExpenseInvalid?: (args: {
    message: string;
    field: ExpenseField;
    reason: ExpenseInvalidReason;
    length: number | null;
  }) => void;
}

interface UseResponseHandlerArgs extends UpdateExpenseCallbacks {
  data: UpdateExpenseMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled UpdateExpenseResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.updateExpense) return;

    const result = data.updateExpense;
    switch (result.__typename) {
      case "Expense":
        callbacks.onExpenseUpdated?.(result);
        return;
      case "ExpenseNotFound":
        callbacks.onExpenseNotFound?.(result.message);
        return;
      case "ExpenseInvalid":
        callbacks.onExpenseInvalid?.({
          message: result.message,
          field: result.field,
          reason: result.reason,
          length: result.length,
        });
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
