/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
export type ExpensePeriodKey =
  | 'ALL_TIME'
  | 'LAST_MONTH'
  | 'LAST_WEEK'
  | 'MONTH'
  | 'THIS_MONTH'
  | 'THIS_WEEK'
  | 'THIS_YEAR'
  | 'TODAY';

export type GetExpensePeriodsQueryVariables = Exact<{ [key: string]: never; }>;


export type GetExpensePeriodsQuery = { expensePeriods: Array<{ key: Types.ExpensePeriodKey, label: string, phrase: string, start: string | null, end: string | null }> };


export const GetExpensePeriodsDocument = gql`
    query GetExpensePeriods {
  expensePeriods {
    key
    label
    phrase
    start
    end
  }
}
    `;