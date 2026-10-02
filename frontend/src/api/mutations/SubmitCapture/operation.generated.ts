/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { TaskFieldsFragmentDoc } from '../../../fragments/TaskFields.generated';
import { ReminderFieldsFragmentDoc } from '../../../fragments/ReminderFields.generated';
import { EventFieldsFragmentDoc } from '../../../fragments/EventFields.generated';
import { MemoryFieldsFragmentDoc } from '../../../fragments/MemoryFields.generated';
import { SearchResultsFieldsFragmentDoc } from '../../../fragments/SearchResultsFields.generated';
export type EventStatusType =
  | 'HAPPENING_NOW'
  | 'PAST'
  | 'UPCOMING';

export type MemoryCategory =
  | 'LIFE'
  | 'PEOPLE'
  | 'PERSONAL'
  | 'PROFESSIONAL';

export type RecordType =
  | 'MEMORY'
  | 'REMINDER'
  | 'TASK';

export type ReminderAction =
  | 'DONE'
  | 'MISSED'
  | 'SNOOZED';

export type ReminderRepeatKind =
  | 'DAILY'
  | 'MONTHLY'
  | 'NONE'
  | 'WEEKLY'
  | 'YEARLY';

export type ReminderState =
  | 'DONE'
  | 'FIRED'
  | 'UPCOMING';

export type SecretKind =
  | 'CARD'
  | 'CREDENTIAL'
  | 'ID_NUMBER'
  | 'TAX_ID';

export type SubmitCaptureMutationVariables = Exact<{
  rawInput: string;
}>;


export type SubmitCaptureMutation = { submitCapture:
    | { __typename: 'EventAlertChoiceAsked', pendingCaptureId: string, question: string, choices: Array<{ leadMinutes: number, label: string }> }
    | { __typename: 'EventCreated', event: { id: string, title: string, location: string | null, startDate: string, startTime: string | null, endDate: string | null, endTime: string | null, allDay: boolean, repeatYearly: boolean, scheduleTimezone: string, startsAt: string, endsAt: string, occurrenceDate: string, occurrenceEndDate: string, whenText: string, alertLeadMinutes: number | null, alertText: string | null, alertFiresAt: string | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNotes: Array<string>, eventDescription: string | null, eventStatus: Types.EventStatusType } }
    | { __typename: 'EventLimitReached', message: string, limit: number }
    | { __typename: 'EventsListed', events: Array<{ id: string, title: string, location: string | null, startDate: string, startTime: string | null, endDate: string | null, endTime: string | null, allDay: boolean, repeatYearly: boolean, scheduleTimezone: string, startsAt: string, endsAt: string, occurrenceDate: string, occurrenceEndDate: string, whenText: string, alertLeadMinutes: number | null, alertText: string | null, alertFiresAt: string | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNotes: Array<string>, eventDescription: string | null, eventStatus: Types.EventStatusType }> }
    | { __typename: 'MalformedResult', message: string, reason: string }
    | { __typename: 'MemoriesListed', searchText: string | null, memories: Array<{ id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }> }
    | { __typename: 'MemoryConflictAsked', pendingCaptureId: string, question: string, newText: string, category: Types.MemoryCategory | null, conflicting: Array<{ id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }> }
    | { __typename: 'MemorySaved', secretCaution: Types.SecretKind | null, memory: { id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string } }
    | { __typename: 'MemoryTooLong', message: string, length: number, limit: number }
    | { __typename: 'NonCommandGuidance', originalInput: string }
    | { __typename: 'PendingQuestionCreated', pendingCaptureId: string, question: string }
    | { __typename: 'ProviderTimeout', message: string, budgetSeconds: number }
    | { __typename: 'ProviderUnavailable', message: string }
    | { __typename: 'ReminderCreated', reminder: { id: string, description: string, state: Types.ReminderState, nextFireAt: string | null, whenText: string, repeatText: string, repeatKind: Types.ReminderRepeatKind, repeatInterval: number, repeatWeekdays: Array<number>, repeatMonthDay: number | null, localTime: string, anchorLocalDate: string, scheduleTimezone: string, lastFiredAt: string | null, lastAction: Types.ReminderAction | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNote: string | null, snoozedUntil: string | null } }
    | { __typename: 'ReminderLimitReached', message: string, limit: number }
    | { __typename: 'RemindersListed', reminders: Array<{ id: string, description: string, state: Types.ReminderState, nextFireAt: string | null, whenText: string, repeatText: string, repeatKind: Types.ReminderRepeatKind, repeatInterval: number, repeatWeekdays: Array<number>, repeatMonthDay: number | null, localTime: string, anchorLocalDate: string, scheduleTimezone: string, lastFiredAt: string | null, lastAction: Types.ReminderAction | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNote: string | null, snoozedUntil: string | null }> }
    | { __typename: 'SearchResults', query: string, meaningUnavailable: boolean, noSupport: boolean, answerUnavailable: boolean, answer: { sentences: Array<{ text: string, citations: Array<number> }> } | null, groups: Array<{ recordType: Types.RecordType, total: number, hits: Array<{ citation: number | null, record:
            | { __typename: 'Memory', id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }
            | { __typename: 'Reminder', id: string, description: string, state: Types.ReminderState, nextFireAt: string | null, whenText: string, repeatText: string, repeatKind: Types.ReminderRepeatKind, repeatInterval: number, repeatWeekdays: Array<number>, repeatMonthDay: number | null, localTime: string, anchorLocalDate: string, scheduleTimezone: string, lastFiredAt: string | null, lastAction: Types.ReminderAction | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNote: string | null, snoozedUntil: string | null }
            | { __typename: 'Task', id: string, title: string, dueAt: string | null, status: string, isOverdue: boolean, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }
           }> }> }
    | { __typename: 'SearchTooLong', length: number, limit: number }
    | { __typename: 'SharedQuotaExhausted', message: string }
    | { __typename: 'TaskCreated', task: { id: string, title: string, dueAt: string | null, status: string, isOverdue: boolean, origin: string, originalInput: string | null, createdAt: string, updatedAt: string } }
    | { __typename: 'TasksListed', tasks: Array<{ id: string, title: string, dueAt: string | null, status: string, isOverdue: boolean, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }> }
    | { __typename: 'UnrecognisedCommand', attemptedName: string, closestMatches: Array<string> }
    | { __typename: 'UserLimitReached', message: string, limit: number, resetsAt: string }
   };


export const SubmitCaptureDocument = gql`
    mutation SubmitCapture($rawInput: String!) {
  submitCapture(rawInput: $rawInput) {
    __typename
    ... on TaskCreated {
      task {
        ...TaskFields
      }
    }
    ... on TasksListed {
      tasks {
        ...TaskFields
      }
    }
    ... on ReminderCreated {
      reminder {
        ...ReminderFields
      }
    }
    ... on RemindersListed {
      reminders {
        ...ReminderFields
      }
    }
    ... on ReminderLimitReached {
      message
      limit
    }
    ... on EventCreated {
      event {
        ...EventFields
      }
    }
    ... on EventsListed {
      events {
        ...EventFields
      }
    }
    ... on EventLimitReached {
      message
      limit
    }
    ... on EventAlertChoiceAsked {
      pendingCaptureId
      question
      choices {
        leadMinutes
        label
      }
    }
    ... on MemorySaved {
      memory {
        ...MemoryFields
      }
      secretCaution
    }
    ... on MemoriesListed {
      memories {
        ...MemoryFields
      }
      searchText
    }
    ... on MemoryTooLong {
      message
      length
      limit
    }
    ... on MemoryConflictAsked {
      pendingCaptureId
      question
      newText
      category
      conflicting {
        ...MemoryFields
      }
    }
    ... on SearchResults {
      ...SearchResultsFields
    }
    ... on SearchTooLong {
      length
      limit
    }
    ... on PendingQuestionCreated {
      pendingCaptureId
      question
    }
    ... on NonCommandGuidance {
      originalInput
    }
    ... on UnrecognisedCommand {
      attemptedName
      closestMatches
    }
    ... on UserLimitReached {
      message
      limit
      resetsAt
    }
    ... on ProviderUnavailable {
      message
    }
    ... on ProviderTimeout {
      message
      budgetSeconds
    }
    ... on SharedQuotaExhausted {
      message
    }
    ... on MalformedResult {
      message
      reason
    }
  }
}
    ${TaskFieldsFragmentDoc}
${ReminderFieldsFragmentDoc}
${EventFieldsFragmentDoc}
${MemoryFieldsFragmentDoc}
${SearchResultsFieldsFragmentDoc}`;