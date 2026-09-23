import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  MarkNotificationReadDocument,
  type MarkNotificationReadMutation,
  type MarkNotificationReadMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type MarkNotificationReadCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends MarkNotificationReadCallbacks {
  id: string;
  onRequestFailed?: (error: Error) => void;
}

interface UseMarkNotificationReadReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useMarkNotificationRead = (): UseMarkNotificationReadReturnType => {
  const [markRead, { data, loading, error }] = useMutation<
    MarkNotificationReadMutation,
    MarkNotificationReadMutationVariables
  >(MarkNotificationReadDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { id, onRequestFailed, ...callbacks } = args;
    markRead({
      variables: { id },
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

export default useMarkNotificationRead;
