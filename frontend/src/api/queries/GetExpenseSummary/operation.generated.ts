/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { ExpenseSummaryFieldsFragmentDoc } from '../../../fragments/ExpenseSummaryFields.generated';
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

export type GetExpenseSummaryQueryVariables = Exact<{
  filter?: Types.ExpensesFilterInput | null | undefined;
}>;


export type GetExpenseSummaryQuery = { expenseSummary: { label: string, phrase: string, start: string | null, end: string | null, count: number, grandTotalPaise: string, totals: Array<{ category: Types.ExpenseCategory, totalPaise: string }> } };


export const GetExpenseSummaryDocument = gql`
    query GetExpenseSummary($filter: ExpensesFilterInput) {
  expenseSummary(filter: $filter) {
    ...ExpenseSummaryFields
  }
}
    ${ExpenseSummaryFieldsFragmentDoc}`;