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

export type SearchRecordsQueryVariables = Exact<{
  text: string;
  recordType?: Types.RecordType | null | undefined;
  offset: number;
  limit: number;
}>;


export type SearchRecordsQuery = { search:
    | { __typename: 'SearchPage', query: string, total: number, otherTypesTotal: number, meaningUnavailable: boolean, hits: Array<
        | { __typename: 'Memory', id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }
        | { __typename: 'Reminder', id: string, description: string, state: Types.ReminderState, nextFireAt: string | null, whenText: string, repeatText: string, repeatKind: Types.ReminderRepeatKind, repeatInterval: number, repeatWeekdays: Array<number>, repeatMonthDay: number | null, localTime: string, anchorLocalDate: string, scheduleTimezone: string, lastFiredAt: string | null, lastAction: Types.ReminderAction | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNote: string | null, snoozedUntil: string | null }
        | { __typename: 'Task', id: string, title: string, dueAt: string | null, status: string, isOverdue: boolean, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }
      > }
    | { __typename: 'SearchTooLong', length: number, limit: number }
   };


export const SearchRecordsDocument = gql`
    query SearchRecords($text: String!, $recordType: RecordType, $offset: Int!, $limit: Int!) {
  search(text: $text, recordType: $recordType, offset: $offset, limit: $limit) {
    __typename
    ... on SearchPage {
      query
      total
      otherTypesTotal
      meaningUnavailable
      hits {
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
    ... on SearchTooLong {
      length
      limit
    }
  }
}
    ${TaskFieldsFragmentDoc}
${ReminderFieldsFragmentDoc}
${MemoryFieldsFragmentDoc}`;