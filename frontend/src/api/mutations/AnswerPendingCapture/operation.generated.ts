/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { TaskFieldsFragmentDoc } from '../../../fragments/TaskFields.generated';
import { ReminderFieldsFragmentDoc } from '../../../fragments/ReminderFields.generated';
import { MemoryFieldsFragmentDoc } from '../../../fragments/MemoryFields.generated';
export type MemoryCategory =
  | 'LIFE'
  | 'PEOPLE'
  | 'PERSONAL'
  | 'PROFESSIONAL';

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

export type AnswerPendingCaptureMutationVariables = Exact<{
  pendingCaptureId: string | number;
  answer: string;
}>;


export type AnswerPendingCaptureMutation = { answerPendingCapture:
    | { __typename: 'ForgetCandidates', totalMatches: number, forgetAll: boolean, allCount: number, forgetText: string, candidates: Array<{ id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }> }
    | { __typename: 'MalformedResult', message: string, reason: string }
    | { __typename: 'MemoriesListed', searchText: string | null, memories: Array<{ id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }> }
    | { __typename: 'MemorySaved', secretCaution: Types.SecretKind | null, memory: { id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string } }
    | { __typename: 'MemoryTooLong', message: string, length: number, limit: number }
    | { __typename: 'NonCommandGuidance', originalInput: string }
    | { __typename: 'PendingQuestionCreated', pendingCaptureId: string, question: string }
    | { __typename: 'ProviderTimeout', message: string, budgetSeconds: number }
    | { __typename: 'ProviderUnavailable', message: string }
    | { __typename: 'ReminderCreated', reminder: { id: string, description: string, state: Types.ReminderState, nextFireAt: string | null, whenText: string, repeatText: string, repeatKind: Types.ReminderRepeatKind, repeatInterval: number, repeatWeekdays: Array<number>, repeatMonthDay: number | null, localTime: string, anchorLocalDate: string, scheduleTimezone: string, lastFiredAt: string | null, lastAction: Types.ReminderAction | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNote: string | null, snoozedUntil: string | null } }
    | { __typename: 'ReminderLimitReached', message: string, limit: number }
    | { __typename: 'RemindersListed', reminders: Array<{ id: string, description: string, state: Types.ReminderState, nextFireAt: string | null, whenText: string, repeatText: string, repeatKind: Types.ReminderRepeatKind, repeatInterval: number, repeatWeekdays: Array<number>, repeatMonthDay: number | null, localTime: string, anchorLocalDate: string, scheduleTimezone: string, lastFiredAt: string | null, lastAction: Types.ReminderAction | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNote: string | null, snoozedUntil: string | null }> }
    | { __typename: 'SharedQuotaExhausted', message: string }
    | { __typename: 'TaskCreated', task: { id: string, title: string, dueAt: string | null, status: string, isOverdue: boolean, origin: string, originalInput: string | null, createdAt: string, updatedAt: string } }
    | { __typename: 'TasksListed', tasks: Array<{ id: string, title: string, dueAt: string | null, status: string, isOverdue: boolean, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }> }
    | { __typename: 'UnrecognisedCommand', attemptedName: string, closestMatches: Array<string> }
    | { __typename: 'UserLimitReached', message: string, limit: number, resetsAt: string }
   };


export const AnswerPendingCaptureDocument = gql`
    mutation AnswerPendingCapture($pendingCaptureId: ID!, $answer: String!) {
  answerPendingCapture(pendingCaptureId: $pendingCaptureId, answer: $answer) {
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
    ... on ForgetCandidates {
      forgetText: searchText
      totalMatches
      forgetAll
      allCount
      candidates {
        ...MemoryFields
      }
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
${MemoryFieldsFragmentDoc}`;