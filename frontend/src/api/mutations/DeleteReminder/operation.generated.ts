/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
export type DeleteReminderMutationVariables = Exact<{
  id: string | number;
}>;


export type DeleteReminderMutation = { deleteReminder:
    | { __typename: 'ReminderDeleteSucceeded', id: string }
    | { __typename: 'ReminderNotFound', message: string }
   };


export const DeleteReminderDocument = gql`
    mutation DeleteReminder($id: ID!) {
  deleteReminder(id: $id) {
    __typename
    ... on ReminderDeleteSucceeded {
      id
    }
    ... on ReminderNotFound {
      message
    }
  }
}
    `;