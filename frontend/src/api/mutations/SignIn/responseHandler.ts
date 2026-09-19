import type { SignInMutation } from "./operation.generated";

export interface SignInCallbacks {
  onSignedIn?: (session: {
    accessToken: string;
    refreshToken: string;
    expiresIn: number;
  }) => void;
  onInvalidCredentials?: (message: string) => void;
  onAccountLocked?: (message: string, retryAfter: string | null) => void;
  onAccountNotVerified?: (message: string) => void;
  onProviderUnavailable?: (message: string) => void;
}

interface UseResponseHandlerArgs extends SignInCallbacks {
  data: SignInMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled SignInResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.signIn) return;

    const result = data.signIn;
    switch (result.__typename) {
      case "SignedIn":
        callbacks.onSignedIn?.({
          accessToken: result.accessToken,
          refreshToken: result.refreshToken,
          expiresIn: result.expiresIn,
        });
        return;
      case "InvalidCredentials":
        callbacks.onInvalidCredentials?.(result.message);
        return;
      case "AccountLocked":
        callbacks.onAccountLocked?.(result.message, result.retryAfter);
        return;
      case "AccountNotVerified":
        callbacks.onAccountNotVerified?.(result.message);
        return;
      case "AuthProviderUnavailable":
        callbacks.onProviderUnavailable?.(result.message);
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
