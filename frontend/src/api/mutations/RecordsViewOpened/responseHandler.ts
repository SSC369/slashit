import type { RecordsViewOpenedMutation } from "./operation.generated";

export interface RecordsViewOpenedCallbacks {
  onLogged?: () => void;
}

interface UseResponseHandlerArgs extends RecordsViewOpenedCallbacks {
  data: RecordsViewOpenedMutation | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onLogged } = args;
    if (!data?.recordsViewOpened) return;
    onLogged?.();
  };

  return { handleResponse };
};
