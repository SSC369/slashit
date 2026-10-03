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

export type ExpensesFilterInput = {
  category?: ExpenseCategory | null | undefined;
  end?: string | null | undefined;
  start?: string | null | undefined;
};

export type GetExpensesQueryVariables = Exact<{
  filter?: Types.ExpensesFilterInput | null | undefined;
}>;


export type GetExpensesQuery = { expenses: Array<{ id: string, amountPaise: string, description: string, category: Types.ExpenseCategory, spentOn: string, origin: string, originalInput: string, createdAt: string, updatedAt: string }> };


export const GetExpensesDocument = gql`
    query GetExpenses($filter: ExpensesFilterInput) {
  expenses(filter: $filter) {
    ...ExpenseFields
  }
}
    ${ExpenseFieldsFragmentDoc}`;