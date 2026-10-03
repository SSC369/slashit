import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import {
  DeleteExpenseDocument,
  type DeleteExpenseMutation,
  type DeleteExpenseMutationVariables,
} from "./operation.generated";
import { useResponseHandler, type DeleteExpenseCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends DeleteExpenseCallbacks {
  id: string;
  onRequestFailed?: (error: Error) => void;
}

interface UseDeleteExpenseReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useDeleteExpense = (): UseDeleteExpenseReturnType => {
  const [deleteExpense, { data, loading, error }] = useMutation<
    DeleteExpenseMutation,
    DeleteExpenseMutationVariables
  >(DeleteExpenseDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { id, onRequestFailed, ...callbacks } = args;
    deleteExpense({
      variables: { id },
      onCompleted: (responseData) => {
        if (!responseData?.deleteExpense) {
          onRequestFailed?.(new Error("The request did not complete. Nothing was deleted."));
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

export default useDeleteExpense;
