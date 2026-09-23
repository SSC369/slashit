/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { ReminderFieldsFragmentDoc } from '../../../fragments/ReminderFields.generated';
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

export type UpdateReminderInput = {
  description: string;
  localTime: string;
  repeatInterval?: number;
  repeatKind: ReminderRepeatKind;
  repeatWeekdays?: Array<number>;
  startDate: string;
};

export type UpdateReminderMutationVariables = Exact<{
  id: string | number;
  input: Types.UpdateReminderInput;
}>;


export type UpdateReminderMutation = { updateReminder:
    | { __typename: 'InvalidReminder', message: string, field: string }
    | { __typename: 'Reminder', id: string, description: string, state: Types.ReminderState, nextFireAt: string | null, whenText: string, repeatText: string, repeatKind: Types.ReminderRepeatKind, repeatInterval: number, repeatWeekdays: Array<number>, repeatMonthDay: number | null, localTime: string, anchorLocalDate: string, scheduleTimezone: string, lastFiredAt: string | null, lastAction: Types.ReminderAction | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNote: string | null }
    | { __typename: 'ReminderDeleted', message: string }
    | { __typename: 'ReminderNotFound', message: string }
    | { __typename: 'ReminderTimePassed', message: string }
   };


export const UpdateReminderDocument = gql`
    mutation UpdateReminder($id: ID!, $input: UpdateReminderInput!) {
  updateReminder(id: $id, input: $input) {
    __typename
    ... on Reminder {
      ...ReminderFields
    }
    ... on InvalidReminder {
      message
      field
    }
    ... on ReminderTimePassed {
      message
    }
    ... on ReminderDeleted {
      message
    }
    ... on ReminderNotFound {
      message
    }
  }
}
    ${ReminderFieldsFragmentDoc}`;