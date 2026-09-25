/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
export type ForgetFromCaptureMutationVariables = Exact<{
  memoryIds: Array<string | number> | string | number;
  forgetAll: boolean;
  expectedCount: number;
}>;


export type ForgetFromCaptureMutation = { forgetFromCapture:
    | { __typename: 'ForgetTargetGone', message: string }
    | { __typename: 'MemoriesForgotten', count: number }
    | { __typename: 'MemoryCountChanged', message: string, count: number }
   };


export const ForgetFromCaptureDocument = gql`
    mutation ForgetFromCapture($memoryIds: [ID!]!, $forgetAll: Boolean!, $expectedCount: Int!) {
  forgetFromCapture(
    memoryIds: $memoryIds
    forgetAll: $forgetAll
    expectedCount: $expectedCount
  ) {
    __typename
    ... on MemoriesForgotten {
      count
    }
    ... on MemoryCountChanged {
      message
      count
    }
    ... on ForgetTargetGone {
      message
    }
  }
}
    `;