import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  UpdateReminderSettingsDocument,
  type UpdateReminderSettingsMutation,
  type UpdateReminderSettingsMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type UpdateReminderSettingsCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends UpdateReminderSettingsCallbacks {
  /** Only the setting that changed; the server keeps the others. */
  input: {
    /** HH:MM, 24-hour. */
    defaultReminderTime?: string;
    popupsEnabled?: boolean;
    emailEnabled?: boolean;
  };
  onRequestFailed?: (error: Error) => void;
}

interface UseUpdateReminderSettingsReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useUpdateReminderSettings = (): UseUpdateReminderSettingsReturnType => {
  const [updateReminderSettings, { data, loading, error }] = useMutation<
    UpdateReminderSettingsMutation,
    UpdateReminderSettingsMutationVariables
  >(UpdateReminderSettingsDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { input, onRequestFailed, ...callbacks } = args;
    updateReminderSettings({
      variables: { input },
      onCompleted: (responseData) => {
        if (!responseData?.updateReminderSettings) {
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

export default useUpdateReminderSettings;
