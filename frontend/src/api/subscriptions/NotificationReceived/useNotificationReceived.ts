import { useSubscription } from "@apollo/client/react";

import {
  NotificationReceivedDocument,
  type NotificationReceivedSubscription,
  type NotificationReceivedSubscriptionVariables,
} from "./operation.generated";
import { useResponseHandler, type NotificationReceivedCallbacks } from "./responseHandler";

interface UseNotificationReceivedArgs extends NotificationReceivedCallbacks {
  /** Held open only while signed in (design §4: never shown signed out). */
  isEnabled: boolean;
}

/**
 * The live feed (FR-13). A pushed notification goes through the same store
 * method the list query fills (repo-rules.md §9), so nothing reconciles a
 * cache. The latest callbacks are read on each push, not captured once.
 */
const useNotificationReceived = (args: UseNotificationReceivedArgs): void => {
  const { isEnabled, ...callbacks } = args;
  const { handleResponse } = useResponseHandler();

  useSubscription<NotificationReceivedSubscription, NotificationReceivedSubscriptionVariables>(
    NotificationReceivedDocument,
    {
      skip: !isEnabled,
      onData: ({ data }) => handleResponse({ data: data.data, ...callbacks }),
    },
  );
};

export default useNotificationReceived;
