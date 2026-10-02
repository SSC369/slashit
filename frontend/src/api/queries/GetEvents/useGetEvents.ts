import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetEventsDocument,
  type GetEventsQuery,
  type GetEventsQueryVariables,
} from "./operation.generated";

interface UseGetEventsReturnType {
  triggerAPI: (variables: GetEventsQueryVariables) => void;
  data: GetEventsQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

/** Same shape as useGetReminders: the caller hands `data` to the response
 * handler in an effect, since Apollo 4's useLazyQuery has no onCompleted. */
const useGetEvents = (): UseGetEventsReturnType => {
  const [getEvents, { data, networkStatus, error }] = useLazyQuery<
    GetEventsQuery,
    GetEventsQueryVariables
  >(GetEventsDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetEventsQueryVariables): void => {
    getEvents({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetEvents;
