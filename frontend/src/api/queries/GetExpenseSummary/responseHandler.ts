import type { ExpenseSummaryFieldsFragment } from "../../../fragments/ExpenseSummaryFields.generated";
import type { GetExpenseSummaryQuery } from "./operation.generated";

export interface GetExpenseSummaryCallbacks {
  onSummaryLoaded?: (summary: ExpenseSummaryFieldsFragment) => void;
}

interface UseResponseHandlerArgs extends GetExpenseSummaryCallbacks {
  data: GetExpenseSummaryQuery | null | undefined;
}

/** `expenseSummary` is one object, not a union; an error arrives as a GraphQL
 * error on the hook instead. */
export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onSummaryLoaded } = args;
    if (!data?.expenseSummary) return;
    onSummaryLoaded?.(data.expenseSummary);
  };

  return { handleResponse };
};
