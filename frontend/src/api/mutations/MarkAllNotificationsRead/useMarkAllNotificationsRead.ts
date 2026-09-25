import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  MarkAllNotificationsReadDocument,
  type MarkAllNotificationsReadMutation,
  type MarkAllNotificationsReadMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type MarkAllNotificationsReadCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends MarkAllNotificationsReadCallbacks {
  onRequestFailed?: (error: Error) => void;
}

interface UseMarkAllNotificationsReadReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useMarkAllNotificationsRead = (): UseMarkAllNotificationsReadReturnType => {
  const [markAllRead, { data, loading, error }] = useMutation<
    MarkAllNotificationsReadMutation,
    MarkAllNotificationsReadMutationVariables
  >(MarkAllNotificationsReadDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { onRequestFailed, ...callbacks } = args;
    markAllRead({
      onCompleted: (responseData) => handleResponse({ data: responseData, ...callbacks }),
      onError: (mutationError) => onRequestFailed?.(mutationError),
    });
  };

  return {
    triggerAPI,
    apiStatus: getAPIStatusFromMutation(loading, data, error),
    apiError: convertToErrorType(error),
  };
};

export default useMarkAllNotificationsRead;
