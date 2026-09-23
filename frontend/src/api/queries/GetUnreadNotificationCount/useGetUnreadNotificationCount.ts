import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetUnreadNotificationCountDocument,
  type GetUnreadNotificationCountQuery,
  type GetUnreadNotificationCountQueryVariables,
} from "./operation.generated";

interface UseGetUnreadNotificationCountReturnType {
  triggerAPI: () => void;
  data: GetUnreadNotificationCountQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useGetUnreadNotificationCount = (): UseGetUnreadNotificationCountReturnType => {
  const [getCount, { data, networkStatus, error }] = useLazyQuery<
    GetUnreadNotificationCountQuery,
    GetUnreadNotificationCountQueryVariables
  >(GetUnreadNotificationCountDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (): void => {
    getCount();
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetUnreadNotificationCount;
