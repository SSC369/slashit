import type { RecordSearchEventMutation } from "./operation.generated";

export interface RecordSearchEventCallbacks {
  onLogged?: () => void;
}

interface UseResponseHandlerArgs extends RecordSearchEventCallbacks {
  data: RecordSearchEventMutation | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onLogged } = args;
    if (!data?.recordSearchEvent) return;
    onLogged?.();
  };

  return { handleResponse };
};
