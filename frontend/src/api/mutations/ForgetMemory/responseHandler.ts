import type { ForgetMemoryMutation } from "./operation.generated";

export interface ForgetMemoryCallbacks {
  onMemoriesForgotten?: (count: number) => void;
  onMemoryNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends ForgetMemoryCallbacks {
  data: ForgetMemoryMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled ForgetMemoryResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.forgetMemory) return;

    const result = data.forgetMemory;
    switch (result.__typename) {
      case "MemoriesForgotten":
        callbacks.onMemoriesForgotten?.(result.count);
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
