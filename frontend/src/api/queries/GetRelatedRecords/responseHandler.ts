import { toRecordItem } from "../../lib/recordItem";
import type { RecordItem } from "../GetRecords/responseHandler";
import type { GetRelatedRecordsQuery } from "./operation.generated";

export interface GetRelatedRecordsCallbacks {
  onRelatedLoaded?: (records: RecordItem[]) => void;
}

interface UseResponseHandlerArgs extends GetRelatedRecordsCallbacks {
  data: GetRelatedRecordsQuery | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onRelatedLoaded } = args;
    if (!data?.relatedRecords) return;
    onRelatedLoaded?.(data.relatedRecords.map(toRecordItem));
  };

  return { handleResponse };
};
