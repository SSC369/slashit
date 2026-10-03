/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { ExpenseFieldsFragmentDoc } from '../../../fragments/ExpenseFields.generated';
export type ExpenseCategory =
  | 'BILLS'
  | 'ENTERTAINMENT'
  | 'FOOD'
  | 'HEALTH'
  | 'OTHER'
  | 'SHOPPING'
  | 'TRANSPORT'
  | 'TRAVEL';

export type GetExpenseQueryVariables = Exact<{
  id: string | number;
}>;


export type GetExpenseQuery = { expense:
    | { __typename: 'Expense', id: string, amountPaise: string, description: string, category: Types.ExpenseCategory, spentOn: string, origin: string, originalInput: string, createdAt: string, updatedAt: string }
    | { __typename: 'ExpenseNotFound', message: string }
   };


export const GetExpenseDocument = gql`
    query GetExpense($id: ID!) {
  expense(id: $id) {
    __typename
    ... on Expense {
      ...ExpenseFields
    }
    ... on ExpenseNotFound {
      message
    }
  }
}
    ${ExpenseFieldsFragmentDoc}`;