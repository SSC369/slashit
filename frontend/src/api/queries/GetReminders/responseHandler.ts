import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import type { GetRemindersQuery } from "./operation.generated";

export interface ReminderGroups {
  needsAttention: ReminderFieldsFragment[];
  upcoming: ReminderFieldsFragment[];
  done: ReminderFieldsFragment[];
}

export interface GetRemindersCallbacks {
  onRemindersLoaded?: (groups: ReminderGroups) => void;
}

interface UseResponseHandlerArgs extends GetRemindersCallbacks {
  data: GetRemindersQuery | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onRemindersLoaded } = args;
    if (!data?.reminders) return;
    const { needsAttention, upcoming, done } = data.reminders;
    onRemindersLoaded?.({ needsAttention, upcoming, done });
  };

  return { handleResponse };
};
