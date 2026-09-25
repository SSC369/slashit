import { useLazyQuery } from "@apollo/client/react";

import { getAPIStatusFromNetworkStatus, type APIStatus } from "../../../constants/apiConstants";
import {
  GetRemindersDocument,
  type GetRemindersQuery,
  type GetRemindersQueryVariables,
} from "./operation.generated";

interface UseGetRemindersReturnType {
  triggerAPI: (variables: GetRemindersQueryVariables) => void;
  data: GetRemindersQuery | undefined;
  apiStatus: APIStatus;
  apiError: Error | null;
}

/** Same shape as useGetRecords: the caller hands `data` to the response
 * handler in an effect, since Apollo 4's useLazyQuery has no onCompleted. */
const useGetReminders = (): UseGetRemindersReturnType => {
  const [getReminders, { data, networkStatus, error }] = useLazyQuery<
    GetRemindersQuery,
    GetRemindersQueryVariables
  >(GetRemindersDocument, {
    fetchPolicy: "network-only",
    notifyOnNetworkStatusChange: true,
  });

  const triggerAPI = (variables: GetRemindersQueryVariables): void => {
    getReminders({ variables });
  };

  return {
    triggerAPI,
    data,
    apiStatus: getAPIStatusFromNetworkStatus(networkStatus, data),
    apiError: error instanceof Error ? error : null,
  };
};

export default useGetReminders;
