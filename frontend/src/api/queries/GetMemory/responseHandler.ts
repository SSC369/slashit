import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import type { GetMemoryQuery } from "./operation.generated";

export interface GetMemoryCallbacks {
  onMemoryLoaded?: (memory: MemoryFieldsFragment) => void;
  onMemoryNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends GetMemoryCallbacks {
  data: GetMemoryQuery | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled MemoryResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.memory) return;

    const result = data.memory;
    switch (result.__typename) {
      case "Memory":
        callbacks.onMemoryLoaded?.(result);
        return;
      case "MemoryNotFound":
        callbacks.onMemoryNotFound?.(result.message);
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
