import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import type { UpdateExpenseInput } from "../../../../types.generated";
import {
  UpdateExpenseDocument,
  type UpdateExpenseMutation,
  type UpdateExpenseMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type UpdateExpenseCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends UpdateExpenseCallbacks {
  id: string;
  /** Only the fields that changed; an absent field is left as it is. */
  input: UpdateExpenseInput;
  onRequestFailed?: (error: Error) => void;
}

interface UseUpdateExpenseReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useUpdateExpense = (): UseUpdateExpenseReturnType => {
  const [updateExpense, { data, loading, error }] = useMutation<
    UpdateExpenseMutation,
    UpdateExpenseMutationVariables
  >(UpdateExpenseDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { id, input, onRequestFailed, ...callbacks } = args;
    updateExpense({
      variables: { id, input },
      onCompleted: (responseData) => {
        if (!responseData?.updateExpense) {
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

export default useUpdateExpense;
