import type { ForgetFromCaptureMutation } from "./operation.generated";

export interface ForgetFromCaptureCallbacks {
  onMemoriesForgotten?: (count: number) => void;
  onMemoryCountChanged?: (args: { message: string; count: number }) => void;
  onForgetTargetGone?: (message: string) => void;
}

interface UseResponseHandlerArgs extends ForgetFromCaptureCallbacks {
  data: ForgetFromCaptureMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled ForgetFromCaptureResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.forgetFromCapture) return;

    const result = data.forgetFromCapture;
    switch (result.__typename) {
      case "MemoriesForgotten":
        callbacks.onMemoriesForgotten?.(result.count);
        return;
      case "MemoryCountChanged":
        callbacks.onMemoryCountChanged?.({ message: result.message, count: result.count });
        return;
      case "ForgetTargetGone":
        callbacks.onForgetTargetGone?.(result.message);
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
