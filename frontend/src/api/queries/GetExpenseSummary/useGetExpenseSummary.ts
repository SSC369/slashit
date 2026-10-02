import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetExpenseSummaryDocument,
  type GetExpenseSummaryQuery,
  type GetExpenseSummaryQueryVariables,
} from "./operation.generated";

interface UseGetExpenseSummaryReturnType {
  triggerAPI: (variables: GetExpenseSummaryQueryVariables) => void;
  data: GetExpenseSummaryQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

/** Same shape as useGetMemories: the caller hands `data` to the response
 * handler in an effect, since Apollo 4's useLazyQuery has no onCompleted. */
const useGetExpenseSummary = (): UseGetExpenseSummaryReturnType => {
  const [getExpenseSummary, { data, networkStatus, error }] = useLazyQuery<
    GetExpenseSummaryQuery,
    GetExpenseSummaryQueryVariables
  >(GetExpenseSummaryDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetExpenseSummaryQueryVariables): void => {
    getExpenseSummary({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetExpenseSummary;
