import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import {
  UpdateReminderDocument,
  type UpdateReminderMutation,
  type UpdateReminderMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type UpdateReminderCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends UpdateReminderCallbacks {
  id: string;
  description: string;
  /** YYYY-MM-DD, in the reminder's own timezone. */
  startDate: string;
  /** HH:MM, 24-hour. */
  localTime: string;
  repeatKind: ReminderFieldsFragment["repeatKind"];
  repeatInterval: number;
  repeatWeekdays: number[];
  onRequestFailed?: (error: Error) => void;
}

interface UseUpdateReminderReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useUpdateReminder = (): UseUpdateReminderReturnType => {
  const [updateReminder, { data, loading, error }] = useMutation<
    UpdateReminderMutation,
    UpdateReminderMutationVariables
  >(UpdateReminderDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const {
      id,
      description,
      startDate,
      localTime,
      repeatKind,
      repeatInterval,
      repeatWeekdays,
      onRequestFailed,
      ...callbacks
    } = args;
    updateReminder({
      variables: {
        id,
        input: { description, startDate, localTime, repeatKind, repeatInterval, repeatWeekdays },
      },
      onCompleted: (responseData) => {
        if (!responseData?.updateReminder) {
          onRequestFailed?.(new Error("The request did not complete. Nothing was saved."));
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

export default useUpdateReminder;
