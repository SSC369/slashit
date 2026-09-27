import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import type { TaskFieldsFragment } from "../../../fragments/TaskFields.generated";
import type { GetRecordsQuery } from "./operation.generated";

/** One row of the All tab: the records union, tagged by `__typename`. */
export type RecordItem =
  | ({ __typename: "Task" } & TaskFieldsFragment)
  | ({ __typename: "Reminder" } & ReminderFieldsFragment)
  | ({ __typename: "Memory" } & MemoryFieldsFragment);

export interface GetRecordsCallbacks {
  onRecordsLoaded?: (records: RecordItem[]) => void;
}

interface UseResponseHandlerArgs extends GetRecordsCallbacks {
  data: GetRecordsQuery | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onRecordsLoaded } = args;
    if (!data?.records) return;
    onRecordsLoaded?.(data.records);
  };

  return { handleResponse };
};
