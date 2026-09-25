import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import type { UpdateMemoryMutation } from "./operation.generated";

export interface UpdateMemoryCallbacks {
  onMemoryUpdated?: (memory: MemoryFieldsFragment) => void;
  onMemoryTooLong?: (args: { message: string; length: number; limit: number }) => void;
  onInvalidMemory?: (message: string) => void;
  onMemoryNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends UpdateMemoryCallbacks {
  data: UpdateMemoryMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled UpdateMemoryResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.updateMemory) return;

    const result = data.updateMemory;
    switch (result.__typename) {
      case "Memory":
        callbacks.onMemoryUpdated?.(result);
        return;
      case "MemoryTooLong":
        callbacks.onMemoryTooLong?.({
          message: result.message,
          length: result.length,
          limit: result.limit,
        });
        return;
      case "InvalidMemory":
        callbacks.onInvalidMemory?.(result.message);
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
