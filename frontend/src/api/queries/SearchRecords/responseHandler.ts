import { toRecordItem } from "../../lib/recordItem";
import type { RecordItem } from "../GetRecords/responseHandler";
import type { SearchRecordsQuery } from "./operation.generated";

export type SearchPageResult = Extract<SearchRecordsQuery["search"], { __typename: "SearchPage" }>;

export interface SearchPageLoaded {
  query: string;
  hits: RecordItem[];
  total: number;
  otherTypesTotal: number;
  meaningUnavailable: boolean;
}

export interface SearchRecordsCallbacks {
  onPageLoaded?: (page: SearchPageLoaded) => void;
  onTooLong?: (length: number, limit: number) => void;
}

interface UseResponseHandlerArgs extends SearchRecordsCallbacks {
  data: SearchRecordsQuery | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled search result: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onPageLoaded, onTooLong } = args;
    if (!data?.search) return;
    const result = data.search;
    switch (result.__typename) {
      case "SearchPage":
        onPageLoaded?.({
          query: result.query,
          hits: result.hits.map(toRecordItem),
          total: result.total,
          otherTypesTotal: result.otherTypesTotal,
          meaningUnavailable: result.meaningUnavailable,
        });
        return;
      case "SearchTooLong":
        onTooLong?.(result.length, result.limit);
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
