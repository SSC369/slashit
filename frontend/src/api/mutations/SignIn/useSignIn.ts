import { useMutation } from "@apollo/client/react";

import { convertToErrorType, getAPIStatusFromMutation, type APIStatus } from "../../../constants/apiConstants";
import { SignInDocument, type SignInMutation, type SignInMutationVariables } from "./operation.generated";
import { useResponseHandler, type SignInCallbacks } from "./responseHandler";

interface TriggerAPIArgs extends SignInCallbacks {
  email: string;
  password: string;
  onRequestFailed?: (error: Error) => void;
}

interface UseSignInReturnType {
  triggerAPI: (args: TriggerAPIArgs) => void;
  apiStatus: APIStatus;
  apiError: Error | null;
}

const useSignIn = (): UseSignInReturnType => {
  const [signIn, { data, loading, error }] = useMutation<
    SignInMutation,
    SignInMutationVariables
  >(SignInDocument);

  const { handleResponse } = useResponseHandler();

  const triggerAPI = (args: TriggerAPIArgs): void => {
    const { email, password, onRequestFailed, ...callbacks } = args;
    signIn({
      variables: { input: { email, password } },
      onCompleted: (responseData) => {
        if (!responseData?.signIn) {
          onRequestFailed?.(new Error("The request did not complete. Nothing was signed in."));
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

export default useSignIn;
