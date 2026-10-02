import type { EventFieldsFragment } from "../../../fragments/EventFields.generated";
import type { GetEventQuery } from "./operation.generated";

export interface GetEventCallbacks {
  onEventLoaded?: (event: EventFieldsFragment) => void;
  onEventNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends GetEventCallbacks {
  data: GetEventQuery | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled EventResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.event) return;

    const result = data.event;
    switch (result.__typename) {
      case "Event":
        callbacks.onEventLoaded?.(result);
        return;
      case "EventNotFound":
        callbacks.onEventNotFound?.(result.message);
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
