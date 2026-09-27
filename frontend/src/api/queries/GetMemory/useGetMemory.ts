import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetMemoryDocument,
  type GetMemoryQuery,
  type GetMemoryQueryVariables,
} from "./operation.generated";

interface UseGetMemoryReturnType {
  triggerAPI: (variables: GetMemoryQueryVariables) => void;
  data: GetMemoryQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useGetMemory = (): UseGetMemoryReturnType => {
  const [getMemory, { data, networkStatus, error }] = useLazyQuery<
    GetMemoryQuery,
    GetMemoryQueryVariables
  >(GetMemoryDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetMemoryQueryVariables): void => {
    getMemory({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetMemory;
