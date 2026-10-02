import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetEventDocument,
  type GetEventQuery,
  type GetEventQueryVariables,
} from "./operation.generated";

interface UseGetEventReturnType {
  triggerAPI: (variables: GetEventQueryVariables) => void;
  data: GetEventQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useGetEvent = (): UseGetEventReturnType => {
  const [getEvent, { data, networkStatus, error }] = useLazyQuery<
    GetEventQuery,
    GetEventQueryVariables
  >(GetEventDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetEventQueryVariables): void => {
    getEvent({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetEvent;
