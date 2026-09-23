import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  DeleteReminderDocument,
  type DeleteReminderMutation,
  type DeleteReminderMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type DeleteReminderCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends DeleteReminderCallbacks {
  id: string;
  onRequestFailed?: (error: Error) => void;
}

interface UseDeleteReminderReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useDeleteReminder = (): UseDeleteReminderReturnType => {
  const [deleteReminder, { data, loading, error }] = useMutation<
    DeleteReminderMutation,
    DeleteReminderMutationVariables
  >(DeleteReminderDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { id, onRequestFailed, ...callbacks } = args;
    deleteReminder({
      variables: { id },
      onCompleted: (responseData) => {
        if (!responseData?.deleteReminder) {
          onRequestFailed?.(new Error("The request did not complete. Nothing was deleted."));
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

export default useDeleteReminder;
