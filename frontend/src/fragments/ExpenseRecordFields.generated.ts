/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../types.generated';

import { gql } from '@apollo/client';
export type ExpenseCategory =
  | 'BILLS'
  | 'ENTERTAINMENT'
  | 'FOOD'
  | 'HEALTH'
  | 'OTHER'
  | 'SHOPPING'
  | 'TRANSPORT'
  | 'TRAVEL';

export type ExpenseRecordFieldsFragment = { id: string, amountPaise: string, description: string, spentOn: string, origin: string, createdAt: string, updatedAt: string, expenseCategory: Types.ExpenseCategory, expenseOriginalInput: string };

export const ExpenseRecordFieldsFragmentDoc = gql`
    fragment ExpenseRecordFields on Expense {
  id
  amountPaise
  description
  expenseCategory: category
  spentOn
  origin
  expenseOriginalInput: originalInput
  createdAt
  updatedAt
}
    `;