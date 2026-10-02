import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetExpensePeriodsDocument,
  type GetExpensePeriodsQuery,
  type GetExpensePeriodsQueryVariables,
} from "./operation.generated";

interface UseGetExpensePeriodsReturnType {
  triggerAPI: (variables: GetExpensePeriodsQueryVariables) => void;
  data: GetExpensePeriodsQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

/** Same shape as useGetExpenses: the caller hands `data` to the response
 * handler in an effect, since Apollo 4's useLazyQuery has no onCompleted. */
const useGetExpensePeriods = (): UseGetExpensePeriodsReturnType => {
  const [getExpensePeriods, { data, networkStatus, error }] = useLazyQuery<
    GetExpensePeriodsQuery,
    GetExpensePeriodsQueryVariables
  >(GetExpensePeriodsDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetExpensePeriodsQueryVariables): void => {
    getExpensePeriods({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetExpensePeriods;
