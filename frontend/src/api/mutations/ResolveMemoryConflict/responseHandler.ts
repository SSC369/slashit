import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import type { SecretKind } from "../../../../types.generated";
import type { ResolveMemoryConflictMutation } from "./operation.generated";

export interface ResolveMemoryConflictCallbacks {
  onMemorySaved?: (args: { memory: MemoryFieldsFragment; secretCaution: SecretKind | null }) => void;
  onMemoryDiscarded?: (message: string) => void;
  onPendingCaptureNotFound?: (message: string) => void;
}

interface UseResponseHandlerArgs extends ResolveMemoryConflictCallbacks {
  data: ResolveMemoryConflictMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled ResolveMemoryConflictResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.resolveMemoryConflict) return;

    const result = data.resolveMemoryConflict;
    switch (result.__typename) {
      case "MemorySaved":
        callbacks.onMemorySaved?.({ memory: result.memory, secretCaution: result.secretCaution });
        return;
      case "MemoryDiscarded":
        callbacks.onMemoryDiscarded?.(result.message);
        return;
      case "PendingCaptureNotFound":
        callbacks.onPendingCaptureNotFound?.(result.message);
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
