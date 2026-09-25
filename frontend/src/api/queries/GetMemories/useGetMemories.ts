import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetMemoriesDocument,
  type GetMemoriesQuery,
  type GetMemoriesQueryVariables,
} from "./operation.generated";

interface UseGetMemoriesReturnType {
  triggerAPI: (variables: GetMemoriesQueryVariables) => void;
  data: GetMemoriesQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

/** Same shape as useGetReminders: the caller hands `data` to the response
 * handler in an effect, since Apollo 4's useLazyQuery has no onCompleted. */
const useGetMemories = (): UseGetMemoriesReturnType => {
  const [getMemories, { data, networkStatus, error }] = useLazyQuery<
    GetMemoriesQuery,
    GetMemoriesQueryVariables
  >(GetMemoriesDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetMemoriesQueryVariables): void => {
    getMemories({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetMemories;
