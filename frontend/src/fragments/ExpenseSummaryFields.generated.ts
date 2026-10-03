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

export type ExpenseSummaryFieldsFragment = { label: string, phrase: string, start: string | null, end: string | null, count: number, grandTotalPaise: string, totals: Array<{ category: Types.ExpenseCategory, totalPaise: string }> };

export const ExpenseSummaryFieldsFragmentDoc = gql`
    fragment ExpenseSummaryFields on ExpenseSummary {
  label
  phrase
  start
  end
  count
  grandTotalPaise
  totals {
    category
    totalPaise
  }
}
    `;