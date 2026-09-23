import type { NotificationFieldsFragment } from "../../../fragments/NotificationFields.generated";
import type { MarkNotificationReadMutation } from "./operation.generated";

export interface MarkNotificationReadCallbacks {
  onNotificationRead?: (notification: NotificationFieldsFragment) => void;
  onNotificationNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends MarkNotificationReadCallbacks {
  data: MarkNotificationReadMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled MarkNotificationReadResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.markNotificationRead) return;

    const result = data.markNotificationRead;
    switch (result.__typename) {
      case "Notification":
        callbacks.onNotificationRead?.(result);
        return;
      case "NotificationNotFound":
        callbacks.onNotificationNotFound?.(result.message);
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
