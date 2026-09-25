import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import type { GetReminderQuery } from "./operation.generated";

export interface GetReminderCallbacks {
  onReminderLoaded?: (reminder: ReminderFieldsFragment) => void;
  onReminderNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends GetReminderCallbacks {
  data: GetReminderQuery | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled ReminderResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.reminder) return;

    const result = data.reminder;
    switch (result.__typename) {
      case "Reminder":
        callbacks.onReminderLoaded?.(result);
        return;
      case "ReminderNotFound":
        callbacks.onReminderNotFound?.(result.message);
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
