import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import type { ConflictAnswer } from "../../../../types.generated";
import {
  ResolveMemoryConflictDocument,
  type ResolveMemoryConflictMutation,
  type ResolveMemoryConflictMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type ResolveMemoryConflictCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends ResolveMemoryConflictCallbacks {
  pendingCaptureId: string;
  answer: ConflictAnswer;
  onRequestFailed?: (error: Error) => void;
}

interface UseResolveMemoryConflictReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useResolveMemoryConflict = (): UseResolveMemoryConflictReturnType => {
  const [resolveMemoryConflict, { data, loading, error }] = useMutation<
    ResolveMemoryConflictMutation,
    ResolveMemoryConflictMutationVariables
  >(ResolveMemoryConflictDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { pendingCaptureId, answer, onRequestFailed, ...callbacks } = args;
    resolveMemoryConflict({
      variables: { pendingCaptureId, answer },
      onCompleted: (responseData) => {
        if (!responseData?.resolveMemoryConflict) {
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

export default useResolveMemoryConflict;
