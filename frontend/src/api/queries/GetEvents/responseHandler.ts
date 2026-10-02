import type { EventFieldsFragment } from "../../../fragments/EventFields.generated";
import type { GetEventsQuery } from "./operation.generated";

export interface GetEventsCallbacks {
  onEventsLoaded?: (events: EventFieldsFragment[]) => void;
}

interface UseResponseHandlerArgs extends GetEventsCallbacks {
  data: GetEventsQuery | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onEventsLoaded } = args;
    if (!data?.events) return;
    onEventsLoaded?.(data.events);
  };

  return { handleResponse };
};
