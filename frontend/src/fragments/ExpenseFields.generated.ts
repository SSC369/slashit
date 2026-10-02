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

export type ExpenseFieldsFragment = { id: string, amountPaise: string, description: string, category: Types.ExpenseCategory, spentOn: string, origin: string, originalInput: string, createdAt: string, updatedAt: string };

export const ExpenseFieldsFragmentDoc = gql`
    fragment ExpenseFields on Expense {
  id
  amountPaise
  description
  category
  spentOn
  origin
  originalInput
  createdAt
  updatedAt
}
    `;