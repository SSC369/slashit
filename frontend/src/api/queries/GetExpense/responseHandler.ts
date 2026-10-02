import type { ExpenseFieldsFragment } from "../../../fragments/ExpenseFields.generated";
import type { GetExpenseQuery } from "./operation.generated";

export interface GetExpenseCallbacks {
  onExpenseLoaded?: (expense: ExpenseFieldsFragment) => void;
  onExpenseNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends GetExpenseCallbacks {
  data: GetExpenseQuery | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled ExpenseResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.expense) return;

    const result = data.expense;
    switch (result.__typename) {
      case "Expense":
        callbacks.onExpenseLoaded?.(result);
        return;
      case "ExpenseNotFound":
        callbacks.onExpenseNotFound?.(result.message);
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
