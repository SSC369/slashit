import type { MarkAllNotificationsReadMutation } from "./operation.generated";

export interface MarkAllNotificationsReadCallbacks {
  onAllRead?: (markedCount: number) => void;
}

interface UseResponseHandlerArgs extends MarkAllNotificationsReadCallbacks {
  data: MarkAllNotificationsReadMutation | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onAllRead } = args;
    if (!data?.markAllNotificationsRead) return;
    onAllRead?.(data.markAllNotificationsRead.markedCount);
  };

  return { handleResponse };
};
