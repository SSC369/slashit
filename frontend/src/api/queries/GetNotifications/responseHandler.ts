import type { NotificationFieldsFragment } from "../../../fragments/NotificationFields.generated";
import type { GetNotificationsQuery } from "./operation.generated";

export interface GetNotificationsCallbacks {
  onNotificationsLoaded?: (items: NotificationFieldsFragment[], nextCursor: string | null) => void;
}

interface UseResponseHandlerArgs extends GetNotificationsCallbacks {
  data: GetNotificationsQuery | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onNotificationsLoaded } = args;
    if (!data?.notifications) return;
    onNotificationsLoaded?.(data.notifications.items, data.notifications.nextCursor);
  };

  return { handleResponse };
};
