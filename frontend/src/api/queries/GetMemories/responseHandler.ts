import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import type { GetMemoriesQuery } from "./operation.generated";

export interface GetMemoriesCallbacks {
  onMemoriesLoaded?: (memories: MemoryFieldsFragment[]) => void;
}

interface UseResponseHandlerArgs extends GetMemoriesCallbacks {
  data: GetMemoriesQuery | null | undefined;
}

/** `memories` is a plain list, not a union, so there is no __typename to
 * switch on; an error arrives as a GraphQL error on the hook instead. */
export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onMemoriesLoaded } = args;
    if (!data?.memories) return;
    onMemoriesLoaded?.(data.memories);
  };

  return { handleResponse };
};
