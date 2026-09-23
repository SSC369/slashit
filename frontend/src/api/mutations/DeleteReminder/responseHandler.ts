import type { DeleteReminderMutation } from "./operation.generated";

export interface DeleteReminderCallbacks {
  onReminderDeleted?: (id: string) => void;
  onReminderNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends DeleteReminderCallbacks {
  data: DeleteReminderMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled DeleteReminderResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.deleteReminder) return;

    const result = data.deleteReminder;
    switch (result.__typename) {
      case "ReminderDeleteSucceeded":
        callbacks.onReminderDeleted?.(result.id);
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
