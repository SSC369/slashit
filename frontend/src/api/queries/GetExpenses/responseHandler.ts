import type { ExpenseFieldsFragment } from "../../../fragments/ExpenseFields.generated";
import type { GetExpensesQuery } from "./operation.generated";

export interface GetExpensesCallbacks {
  onExpensesLoaded?: (expenses: ExpenseFieldsFragment[]) => void;
}

interface UseResponseHandlerArgs extends GetExpensesCallbacks {
  data: GetExpensesQuery | null | undefined;
}

/** `expenses` is a plain list, not a union, so there is no __typename to
 * switch on; an error arrives as a GraphQL error on the hook instead. */
export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onExpensesLoaded } = args;
    if (!data?.expenses) return;
    onExpensesLoaded?.(data.expenses);
  };

  return { handleResponse };
};
