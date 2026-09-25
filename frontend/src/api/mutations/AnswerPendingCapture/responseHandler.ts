import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import type { ForgetCandidatesArgs } from "../../../constants/memoryConstants";
import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import type { SecretKind } from "../../../../types.generated";
import type { TaskFieldsFragment } from "../../../fragments/TaskFields.generated";
import type { AnswerPendingCaptureMutation } from "./operation.generated";

export interface AnswerPendingCaptureCallbacks {
  onTaskCreated?: (task: TaskFieldsFragment) => void;
  onTasksListed?: (tasks: TaskFieldsFragment[]) => void;
  onReminderCreated?: (reminder: ReminderFieldsFragment) => void;
  onRemindersListed?: (reminders: ReminderFieldsFragment[]) => void;
  onReminderLimitReached?: (args: { message: string; limit: number }) => void;
  onMemorySaved?: (args: { memory: MemoryFieldsFragment; secretCaution: SecretKind | null }) => void;
  onMemoriesListed?: (args: { memories: MemoryFieldsFragment[]; searchText: string | null }) => void;
  onMemoryTooLong?: (args: { message: string; length: number; limit: number }) => void;
  onForgetCandidates?: (args: ForgetCandidatesArgs) => void;
  onPendingQuestionCreated?: (args: { pendingCaptureId: string; question: string }) => void;
  onNonCommandGuidance?: (originalInput: string) => void;
  onUnrecognisedCommand?: (args: { attemptedName: string; closestMatches: string[] }) => void;
  onUserLimitReached?: (args: { message: string; limit: number; resetsAt: string }) => void;
  onProviderUnavailable?: (message: string) => void;
  onProviderTimeout?: (args: { message: string; budgetSeconds: number }) => void;
  onSharedQuotaExhausted?: (message: string) => void;
  onMalformedResult?: (args: { message: string; reason: string }) => void;
}

interface UseResponseHandlerArgs extends AnswerPendingCaptureCallbacks {
  data: AnswerPendingCaptureMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled CaptureResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): { handleResponse: (args: UseResponseHandlerArgs) => void } => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.answerPendingCapture) return;

    const result = data.answerPendingCapture;
    switch (result.__typename) {
      case "TaskCreated":
        callbacks.onTaskCreated?.(result.task);
        return;
      case "TasksListed":
        callbacks.onTasksListed?.(result.tasks);
        return;
      case "ReminderCreated":
        callbacks.onReminderCreated?.(result.reminder);
        return;
      case "RemindersListed":
        callbacks.onRemindersListed?.(result.reminders);
        return;
      case "ReminderLimitReached":
        callbacks.onReminderLimitReached?.({ message: result.message, limit: result.limit });
        return;
      case "MemorySaved":
        callbacks.onMemorySaved?.({ memory: result.memory, secretCaution: result.secretCaution });
        return;
      case "MemoriesListed":
        callbacks.onMemoriesListed?.({ memories: result.memories, searchText: result.searchText });
        return;
      case "MemoryTooLong":
        callbacks.onMemoryTooLong?.({
          message: result.message,
          length: result.length,
          limit: result.limit,
        });
        return;
      case "ForgetCandidates":
        callbacks.onForgetCandidates?.({
          searchText: result.forgetText,
          candidates: result.candidates,
          totalMatches: result.totalMatches,
          forgetAll: result.forgetAll,
          allCount: result.allCount,
        });
        return;
      case "PendingQuestionCreated":
        callbacks.onPendingQuestionCreated?.({
          pendingCaptureId: result.pendingCaptureId,
          question: result.question,
        });
        return;
      case "NonCommandGuidance":
        callbacks.onNonCommandGuidance?.(result.originalInput);
        return;
      case "UnrecognisedCommand":
        callbacks.onUnrecognisedCommand?.({
          attemptedName: result.attemptedName,
          closestMatches: result.closestMatches,
        });
        return;
      case "UserLimitReached":
        callbacks.onUserLimitReached?.({
          message: result.message,
          limit: result.limit,
          resetsAt: result.resetsAt,
        });
        return;
      case "ProviderUnavailable":
        callbacks.onProviderUnavailable?.(result.message);
        return;
      case "ProviderTimeout":
        callbacks.onProviderTimeout?.({
          message: result.message,
          budgetSeconds: result.budgetSeconds,
        });
        return;
      case "SharedQuotaExhausted":
        callbacks.onSharedQuotaExhausted?.(result.message);
        return;
      case "MalformedResult":
        callbacks.onMalformedResult?.({ message: result.message, reason: result.reason });
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
