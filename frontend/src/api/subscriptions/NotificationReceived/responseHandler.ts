import type { NotificationFieldsFragment } from "../../../fragments/NotificationFields.generated";
import type { NotificationReceivedSubscription } from "./operation.generated";

export interface NotificationReceivedCallbacks {
  onNotificationReceived?: (notification: NotificationFieldsFragment) => void;
}

interface UseResponseHandlerArgs extends NotificationReceivedCallbacks {
  data: NotificationReceivedSubscription | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onNotificationReceived } = args;
    if (!data?.notificationReceived) return;
    onNotificationReceived?.(data.notificationReceived);
  };

  return { handleResponse };
};
