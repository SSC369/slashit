import type { GetUnreadNotificationCountQuery } from "./operation.generated";

export interface GetUnreadNotificationCountCallbacks {
  onCountLoaded?: (count: number) => void;
}

interface UseResponseHandlerArgs extends GetUnreadNotificationCountCallbacks {
  data: GetUnreadNotificationCountQuery | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onCountLoaded } = args;
    if (data === null || data === undefined) return;
    onCountLoaded?.(data.unreadNotificationCount);
  };

  return { handleResponse };
};
