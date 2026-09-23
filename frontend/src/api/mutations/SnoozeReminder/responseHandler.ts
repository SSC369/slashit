import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import type { SnoozeReminderMutation } from "./operation.generated";

export interface SnoozeReminderCallbacks {
  onReminderActed?: (reminder: ReminderFieldsFragment) => void;
  onReminderNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends SnoozeReminderCallbacks {
  data: SnoozeReminderMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled ReminderActionResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.snoozeReminder) return;

    const result = data.snoozeReminder;
    switch (result.__typename) {
      case "Reminder":
        callbacks.onReminderActed?.(result);
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
