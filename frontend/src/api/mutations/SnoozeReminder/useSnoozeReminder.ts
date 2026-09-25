import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  SnoozeReminderDocument,
  type SnoozeReminderMutation,
  type SnoozeReminderMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type SnoozeReminderCallbacks } from "./responseHandler";

export type SnoozeChoiceType = SnoozeReminderMutationVariables["option"];

interface TriggerAPIArgs extends SnoozeReminderCallbacks {
  id: string;
  option: SnoozeChoiceType;
  onRequestFailed?: (error: Error) => void;
}

interface UseSnoozeReminderReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useSnoozeReminder = (): UseSnoozeReminderReturnType => {
  const [snooze, { data, loading, error }] = useMutation<
    SnoozeReminderMutation,
    SnoozeReminderMutationVariables
  >(SnoozeReminderDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { id, option, onRequestFailed, ...callbacks } = args;
    snooze({
      variables: { id, option },
      onCompleted: (responseData) => {
        if (!responseData?.snoozeReminder) {
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

export default useSnoozeReminder;
