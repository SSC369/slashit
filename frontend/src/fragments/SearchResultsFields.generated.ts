/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../types.generated';

import { gql } from '@apollo/client';
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
  | 'EVENT'
  | 'EXPENSE'
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
        | { __typename: 'Event', id: string, title: string, location: string | null, startDate: string, startTime: string | null, endDate: string | null, endTime: string | null, allDay: boolean, repeatYearly: boolean, scheduleTimezone: string, startsAt: string, endsAt: string, occurrenceDate: string, occurrenceEndDate: string, whenText: string, alertNotes: Array<string>, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNotes: Array<string>, eventDescription: string | null, eventStatus: Types.EventStatusType, alerts: Array<{ leadMinutes: number, text: string, firesAt: string }> }
        | { __typename: 'Expense', id: string, amountPaise: string, description: string, spentOn: string }
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
        ... on Event {
          ...EventFields
        }
        ... on Expense {
          id
          amountPaise
          description
          spentOn
        }
      }
    }
  }
}
    `;