import type { GetExpensePeriodsQuery } from "./operation.generated";

export type ExpensePeriodFragment = GetExpensePeriodsQuery["expensePeriods"][number];

export interface GetExpensePeriodsCallbacks {
  onPeriodsLoaded?: (periods: ExpensePeriodFragment[]) => void;
}

interface UseResponseHandlerArgs extends GetExpensePeriodsCallbacks {
  data: GetExpensePeriodsQuery | null | undefined;
}

/** `expensePeriods` is a plain list, not a union, so there is no __typename
 * to switch on; an error arrives as a GraphQL error on the hook instead. */
export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onPeriodsLoaded } = args;
    if (!data?.expensePeriods) return;
    onPeriodsLoaded?.(data.expensePeriods);
  };

  return { handleResponse };
};
