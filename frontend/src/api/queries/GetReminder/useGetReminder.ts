import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetReminderDocument,
  type GetReminderQuery,
  type GetReminderQueryVariables,
} from "./operation.generated";

interface UseGetReminderReturnType {
  triggerAPI: (variables: GetReminderQueryVariables) => void;
  data: GetReminderQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useGetReminder = (): UseGetReminderReturnType => {
  const [getReminder, { data, networkStatus, error }] = useLazyQuery<
    GetReminderQuery,
    GetReminderQueryVariables
  >(GetReminderDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetReminderQueryVariables): void => {
    getReminder({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetReminder;
