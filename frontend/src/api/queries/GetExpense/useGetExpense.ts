import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetExpenseDocument,
  type GetExpenseQuery,
  type GetExpenseQueryVariables,
} from "./operation.generated";

interface UseGetExpenseReturnType {
  triggerAPI: (variables: GetExpenseQueryVariables) => void;
  data: GetExpenseQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useGetExpense = (): UseGetExpenseReturnType => {
  const [getExpense, { data, networkStatus, error }] = useLazyQuery<
    GetExpenseQuery,
    GetExpenseQueryVariables
  >(GetExpenseDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetExpenseQueryVariables): void => {
    getExpense({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetExpense;
