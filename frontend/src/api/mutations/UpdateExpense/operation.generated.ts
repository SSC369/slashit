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

export type ExpenseField =
  | 'AMOUNT'
  | 'DESCRIPTION';

export type ExpenseInvalidReason =
  | 'EMPTY'
  | 'NOT_POSITIVE'
  | 'TOO_LARGE'
  | 'TOO_LONG';

export type UpdateExpenseInput = {
  amountPaise?: string | null | undefined;
  category?: ExpenseCategory | null | undefined;
  description?: string | null | undefined;
  spentOn?: string | null | undefined;
};

export type UpdateExpenseMutationVariables = Exact<{
  id: string | number;
  input: Types.UpdateExpenseInput;
}>;


export type UpdateExpenseMutation = { updateExpense:
    | { __typename: 'Expense', id: string, amountPaise: string, description: string, category: Types.ExpenseCategory, spentOn: string, origin: string, originalInput: string, createdAt: string, updatedAt: string }
    | { __typename: 'ExpenseInvalid', message: string, field: Types.ExpenseField, reason: Types.ExpenseInvalidReason, length: number | null }
    | { __typename: 'ExpenseNotFound', message: string }
   };


export const UpdateExpenseDocument = gql`
    mutation UpdateExpense($id: ID!, $input: UpdateExpenseInput!) {
  updateExpense(id: $id, input: $input) {
    __typename
    ... on Expense {
      ...ExpenseFields
    }
    ... on ExpenseNotFound {
      message
    }
    ... on ExpenseInvalid {
      message
      field
      reason
      length
    }
  }
}
    ${ExpenseFieldsFragmentDoc}`;