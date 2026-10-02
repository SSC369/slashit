/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../types.generated';

import { gql } from '@apollo/client';
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

export type SearchResultsFieldsFragment = { query: string, meaningUnavailable: boolean, noSupport: boolean, answerUnavailable: boolean, answerLimitReached: boolean, answer: { sentences: Array<{ text: string, citations: Array<number> }> } | null, groups: Array<{ recordType: Types.RecordType, total: number, hits: Array<{ citation: number | null, record:
        | { __typename: 'Memory', id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }
        | { __typename: 'Reminder', id: string, description: string, state: Types.ReminderState, nextFireAt: string | null, whenText: string, repeatText: string, repeatKind: Types.ReminderRepeatKind, repeatInterval: number, repeatWeekdays: Array<number>, repeatMonthDay: number | null, localTime: string, anchorLocalDate: string, scheduleTimezone: string, lastFiredAt: string | null, lastAction: Types.ReminderAction | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNote: string | null, snoozedUntil: string | null }
        | { __typename: 'Task', id: string, title: string, dueAt: string | null, status: string, isOverdue: boolean, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }
       }> }> };

export const SearchResultsFieldsFragmentDoc = gql`
    fragment SearchResultsFields on SearchResults {
  query
  meaningUnavailable
  noSupport
  answerUnavailable
  answerLimitReached
  answer {
    sentences {
      text
      citations
    }
  }
  groups {
    recordType
    total
    hits {
      citation
      record {
        __typename
        ... on Task {
          ...TaskFields
        }
        ... on Reminder {
          ...ReminderFields
        }
        ... on Memory {
          ...MemoryFields
        }
      }
    }
  }
}
    `;