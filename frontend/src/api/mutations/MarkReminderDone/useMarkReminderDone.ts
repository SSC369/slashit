import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  MarkReminderDoneDocument,
  type MarkReminderDoneMutation,
  type MarkReminderDoneMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type MarkReminderDoneCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends MarkReminderDoneCallbacks {
  id: string;
  /** A network or server failure: nothing changed (`PopupFailed`). */
  onRequestFailed?: (error: Error) => void;
}

interface UseMarkReminderDoneReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useMarkReminderDone = (): UseMarkReminderDoneReturnType => {
  const [markDone, { data, loading, error }] = useMutation<
    MarkReminderDoneMutation,
    MarkReminderDoneMutationVariables
  >(MarkReminderDoneDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { id, onRequestFailed, ...callbacks } = args;
    markDone({
      variables: { id },
      onCompleted: (responseData) => {
        if (!responseData?.markReminderDone) {
          onRequestFailed?.(new Error("The request did not complete. Nothing changed."));
          return;
        }
        handleResponse({ data: responseData, ...callbacks });
      },
      onError: (mutationError) => onRequestFailed?.(mutationError),
    });
  };

  return {
    triggerAPI,
    apiStatus: getAPIStatusFromMutation(loading, data, error),
    apiError: convertToErrorType(error),
  };
};

export default useMarkReminderDone;
