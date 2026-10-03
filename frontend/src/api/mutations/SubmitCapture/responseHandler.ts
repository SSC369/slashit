import type { EventCreatedArgs } from "../../../constants/eventConstants";
import type { EventFieldsFragment } from "../../../fragments/EventFields.generated";
import type { ExpenseFieldsFragment } from "../../../fragments/ExpenseFields.generated";
import type { ExpenseSummaryFieldsFragment } from "../../../fragments/ExpenseSummaryFields.generated";
import type { ExpenseQuestionArgs, ExpenseRefusalArgs } from "../../../constants/expenseConstants";
import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import type { MemoryConflictArgs } from "../../../constants/memoryConstants";
import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import type { SearchResultsFieldsFragment } from "../../../fragments/SearchResultsFields.generated";
import type { SecretKind } from "../../../../types.generated";
import type { TaskFieldsFragment } from "../../../fragments/TaskFields.generated";
import type { SubmitCaptureMutation } from "./operation.generated";

export interface SubmitCaptureCallbacks {
  onTaskCreated?: (task: TaskFieldsFragment) => void;
  onTasksListed?: (tasks: TaskFieldsFragment[]) => void;
  onReminderCreated?: (reminder: ReminderFieldsFragment) => void;
  onRemindersListed?: (reminders: ReminderFieldsFragment[]) => void;
  onReminderLimitReached?: (args: { message: string; limit: number }) => void;
  onEventCreated?: (args: EventCreatedArgs) => void;
  onEventsListed?: (events: EventFieldsFragment[]) => void;
  onEventLimitReached?: (args: { message: string; limit: number }) => void;
  onMemorySaved?: (args: { memory: MemoryFieldsFragment; secretCaution: SecretKind | null }) => void;
  onMemoriesListed?: (args: { memories: MemoryFieldsFragment[]; searchText: string | null }) => void;
  onMemoryTooLong?: (args: { message: string; length: number; limit: number }) => void;
  onMemoryConflictAsked?: (args: MemoryConflictArgs) => void;
  onSearchResults?: (results: SearchResultsFieldsFragment) => void;
  onSearchTooLong?: (args: { length: number; limit: number }) => void;
  onExpenseSaved?: (expense: ExpenseFieldsFragment) => void;
  onExpenseQuestionAsked?: (args: ExpenseQuestionArgs) => void;
  onExpenseRefused?: (args: ExpenseRefusalArgs) => void;
  onExpenseSummary?: (summary: ExpenseSummaryFieldsFragment) => void;
  onPendingQuestionCreated?: (args: { pendingCaptureId: string; question: string }) => void;
  onNonCommandGuidance?: (originalInput: string) => void;
  onUnrecognisedCommand?: (args: { attemptedName: string; closestMatches: string[] }) => void;
  onUserLimitReached?: (args: { message: string; limit: number; resetsAt: string }) => void;
  onProviderUnavailable?: (message: string) => void;
  onProviderTimeout?: (args: { message: string; budgetSeconds: number }) => void;
  onSharedQuotaExhausted?: (message: string) => void;
  onMalformedResult?: (args: { message: string; reason: string }) => void;
}

interface UseResponseHandlerArgs extends SubmitCaptureCallbacks {
  data: SubmitCaptureMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled CaptureResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): { handleResponse: (args: UseResponseHandlerArgs) => void } => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.submitCapture) return;

    const result = data.submitCapture;
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
      case "EventCreated":
        callbacks.onEventCreated?.({ event: result.event, alertsNotSet: result.alertsNotSet });
        return;
      case "EventsListed":
        callbacks.onEventsListed?.(result.events);
        return;
      case "EventLimitReached":
        callbacks.onEventLimitReached?.({ message: result.message, limit: result.limit });
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
      case "MemoryConflictAsked":
        callbacks.onMemoryConflictAsked?.({
          pendingCaptureId: result.pendingCaptureId,
          newText: result.newText,
          category: result.category,
          conflicting: result.conflicting,
        });
        return;
      case "SearchResults":
        callbacks.onSearchResults?.(result);
        return;
      case "SearchTooLong":
        callbacks.onSearchTooLong?.({ length: result.length, limit: result.limit });
        return;
      case "ExpenseSaved":
        callbacks.onExpenseSaved?.(result.expense);
        return;
      case "ExpenseQuestionAsked":
        callbacks.onExpenseQuestionAsked?.({
          pendingCaptureId: result.pendingCaptureId,
          kind: result.kind,
          question: result.question,
          amountCandidates: result.amountCandidates,
          readDate: result.readDate,
        });
        return;
      case "ExpenseRefused":
        callbacks.onExpenseRefused?.({
          message: result.message,
          reason: result.refusalReason,
          length: result.descriptionLength,
        });
        return;
      case "ExpenseSummary":
        callbacks.onExpenseSummary?.(result);
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
