import type { DeleteExpenseMutation } from "./operation.generated";

export interface DeleteExpenseCallbacks {
  onExpenseDeleted?: (id: string) => void;
  onExpenseNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends DeleteExpenseCallbacks {
  data: DeleteExpenseMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled DeleteExpenseResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.deleteExpense) return;

    const result = data.deleteExpense;
    switch (result.__typename) {
      case "ExpenseDeleted":
        callbacks.onExpenseDeleted?.(result.id);
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
