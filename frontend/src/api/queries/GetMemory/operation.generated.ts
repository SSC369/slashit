/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { MemoryFieldsFragmentDoc } from '../../../fragments/MemoryFields.generated';
export type MemoryCategory =
  | 'LIFE'
  | 'PEOPLE'
  | 'PERSONAL'
  | 'PROFESSIONAL';

export type GetMemoryQueryVariables = Exact<{
  id: string | number;
}>;


export type GetMemoryQuery = { memory:
    | { __typename: 'Memory', id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }
    | { __typename: 'MemoryNotFound', message: string }
   };


export const GetMemoryDocument = gql`
    query GetMemory($id: ID!) {
  memory(id: $id) {
    __typename
    ... on Memory {
      ...MemoryFields
    }
    ... on MemoryNotFound {
      message
    }
  }
}
    ${MemoryFieldsFragmentDoc}`;