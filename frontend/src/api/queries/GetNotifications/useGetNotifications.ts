import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetNotificationsDocument,
  type GetNotificationsQuery,
  type GetNotificationsQueryVariables,
} from "./operation.generated";

interface UseGetNotificationsReturnType {
  triggerAPI: (variables: GetNotificationsQueryVariables) => void;
  data: GetNotificationsQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useGetNotifications = (): UseGetNotificationsReturnType => {
  const [getNotifications, { data, networkStatus, error }] = useLazyQuery<
    GetNotificationsQuery,
    GetNotificationsQueryVariables
  >(GetNotificationsDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetNotificationsQueryVariables): void => {
    getNotifications({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetNotifications;
