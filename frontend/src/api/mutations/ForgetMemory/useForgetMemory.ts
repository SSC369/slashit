import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  ForgetMemoryDocument,
  type ForgetMemoryMutation,
  type ForgetMemoryMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type ForgetMemoryCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends ForgetMemoryCallbacks {
  id: string;
  onRequestFailed?: (error: Error) => void;
}

interface UseForgetMemoryReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useForgetMemory = (): UseForgetMemoryReturnType => {
  const [forgetMemory, { data, loading, error }] = useMutation<
    ForgetMemoryMutation,
    ForgetMemoryMutationVariables
  >(ForgetMemoryDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { id, onRequestFailed, ...callbacks } = args;
    forgetMemory({
      variables: { id },
      onCompleted: (responseData) => {
        if (!responseData?.forgetMemory) {
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

export default useForgetMemory;
