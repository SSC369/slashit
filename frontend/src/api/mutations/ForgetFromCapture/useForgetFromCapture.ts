import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  ForgetFromCaptureDocument,
  type ForgetFromCaptureMutation,
  type ForgetFromCaptureMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type ForgetFromCaptureCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends ForgetFromCaptureCallbacks {
  memoryIds: string[];
  forgetAll: boolean;
  /** For forget-all: the count the user confirmed (FR-27's guard). */
  expectedCount: number;
  onRequestFailed?: (error: Error) => void;
}

interface UseForgetFromCaptureReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useForgetFromCapture = (): UseForgetFromCaptureReturnType => {
  const [forgetFromCapture, { data, loading, error }] = useMutation<
    ForgetFromCaptureMutation,
    ForgetFromCaptureMutationVariables
  >(ForgetFromCaptureDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { memoryIds, forgetAll, expectedCount, onRequestFailed, ...callbacks } = args;
    forgetFromCapture({
      variables: { memoryIds, forgetAll, expectedCount },
      onCompleted: (responseData) => {
        if (!responseData?.forgetFromCapture) {
          onRequestFailed?.(new Error("The request did not complete. Nothing was forgotten."));
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

export default useForgetFromCapture;
