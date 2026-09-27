import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import type { MemoryCategory } from "../../../../types.generated";
import {
  UpdateMemoryDocument,
  type UpdateMemoryMutation,
  type UpdateMemoryMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type UpdateMemoryCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends UpdateMemoryCallbacks {
  id: string;
  text: string;
  category: MemoryCategory | null;
  onRequestFailed?: (error: Error) => void;
}

interface UseUpdateMemoryReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useUpdateMemory = (): UseUpdateMemoryReturnType => {
  const [updateMemory, { data, loading, error }] = useMutation<
    UpdateMemoryMutation,
    UpdateMemoryMutationVariables
  >(UpdateMemoryDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { id, text, category, onRequestFailed, ...callbacks } = args;
    updateMemory({
      variables: { id, input: { text, category } },
      onCompleted: (responseData) => {
        if (!responseData?.updateMemory) {
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

export default useUpdateMemory;
