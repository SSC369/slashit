import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetExpensesDocument,
  type GetExpensesQuery,
  type GetExpensesQueryVariables,
} from "./operation.generated";

interface UseGetExpensesReturnType {
  triggerAPI: (variables: GetExpensesQueryVariables) => void;
  data: GetExpensesQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

/** Same shape as useGetMemories: the caller hands `data` to the response
 * handler in an effect, since Apollo 4's useLazyQuery has no onCompleted. */
const useGetExpenses = (): UseGetExpensesReturnType => {
  const [getExpenses, { data, networkStatus, error }] = useLazyQuery<
    GetExpensesQuery,
    GetExpensesQueryVariables
  >(GetExpensesDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetExpensesQueryVariables): void => {
    getExpenses({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetExpenses;
