import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  RecordsViewOpenedDocument,
  type RecordsViewOpenedMutation,
  type RecordsViewOpenedMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type RecordsViewOpenedCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends RecordsViewOpenedCallbacks {
  onRequestFailed?: (error: Error) => void;
}

interface UseRecordsViewOpenedReturnType {
  triggerAPI: (args?: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useRecordsViewOpened = (): UseRecordsViewOpenedReturnType => {
  const [recordsViewOpened, { data, loading, error }] = useMutation<
    RecordsViewOpenedMutation,
    RecordsViewOpenedMutationVariables
  >(RecordsViewOpenedDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs = {}): void => {
    const { onRequestFailed, ...callbacks } = args;
    recordsViewOpened({
      onCompleted: (responseData) => handleResponse({ data: responseData, ...callbacks }),
      // Instrumentation only: a failed write never surfaces to the user,
      // same reasoning as the backend's non-blocking analytics writes.
      onError: (mutationError) => onRequestFailed?.(mutationError),
    });
  };

  return {
    triggerAPI,
    apiStatus: getAPIStatusFromMutation(loading, data, error),
    apiError: convertToErrorType(error),
  };
};

export default useRecordsViewOpened;
