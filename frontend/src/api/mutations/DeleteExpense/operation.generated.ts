/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
export type DeleteExpenseMutationVariables = Exact<{
  id: string | number;
}>;


export type DeleteExpenseMutation = { deleteExpense:
    | { __typename: 'ExpenseDeleted', id: string }
    | { __typename: 'ExpenseNotFound', message: string }
   };


export const DeleteExpenseDocument = gql`
    mutation DeleteExpense($id: ID!) {
  deleteExpense(id: $id) {
    __typename
    ... on ExpenseDeleted {
      id
    }
    ... on ExpenseNotFound {
      message
    }
  }
}
    `;