/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
export type ForgetMemoryMutationVariables = Exact<{
  id: string | number;
}>;


export type ForgetMemoryMutation = { forgetMemory:
    | { __typename: 'MemoriesForgotten', count: number }
    | { __typename: 'MemoryNotFound', message: string }
   };


export const ForgetMemoryDocument = gql`
    mutation ForgetMemory($id: ID!) {
  forgetMemory(id: $id) {
    __typename
    ... on MemoriesForgotten {
      count
    }
    ... on MemoryNotFound {
      message
    }
  }
}
    `;