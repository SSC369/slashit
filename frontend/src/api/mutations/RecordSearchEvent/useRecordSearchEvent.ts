import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import type { SearchEventKind } from "../../../../types.generated";
import {
  RecordSearchEventDocument,
  type RecordSearchEventMutation,
  type RecordSearchEventMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type RecordSearchEventCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends RecordSearchEventCallbacks {
  kind: SearchEventKind;
  /** 1-based: a row's place down the card, or a citation's number. */
  position: number;
  onRequestFailed?: (error: Error) => void;
}

interface UseRecordSearchEventReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useRecordSearchEvent = (): UseRecordSearchEventReturnType => {
  const [recordSearchEvent, { data, loading, error }] = useMutation<
    RecordSearchEventMutation,
    RecordSearchEventMutationVariables
  >(RecordSearchEventDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { kind, position, onRequestFailed, ...callbacks } = args;
    recordSearchEvent({
      variables: { input: { kind, position } },
      onCompleted: (responseData) => handleResponse({ data: responseData, ...callbacks }),
      // Instrumentation only: a failed write never surfaces to the user
      // (sub-plan 4.2 §6).
      onError: (mutationError) => onRequestFailed?.(mutationError),
    });
  };

  return {
    triggerAPI,
    apiStatus: getAPIStatusFromMutation(loading, data, error),
    apiError: convertToErrorType(error),
  };
};

export default useRecordSearchEvent;
