import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import type { UpdateReminderMutation } from "./operation.generated";

export interface UpdateReminderCallbacks {
  onReminderUpdated?: (reminder: ReminderFieldsFragment) => void;
  onInvalidReminder?: (args: { field: string; message: string }) => void;
  onReminderTimePassed?: (message: string) => void;
  onReminderDeleted?: (message: string) => void;
  onReminderNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends UpdateReminderCallbacks {
  data: UpdateReminderMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled UpdateReminderResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.updateReminder) return;

    const result = data.updateReminder;
    switch (result.__typename) {
      case "Reminder":
        callbacks.onReminderUpdated?.(result);
        return;
      case "InvalidReminder":
        callbacks.onInvalidReminder?.({ field: result.field, message: result.message });
        return;
      case "ReminderTimePassed":
        callbacks.onReminderTimePassed?.(result.message);
        return;
      case "ReminderDeleted":
        callbacks.onReminderDeleted?.(result.message);
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
