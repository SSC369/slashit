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

export type UpdateMemoryInput = {
  category?: MemoryCategory | null | undefined;
  text: string;
};

export type UpdateMemoryMutationVariables = Exact<{
  id: string | number;
  input: Types.UpdateMemoryInput;
}>;


export type UpdateMemoryMutation = { updateMemory:
    | { __typename: 'InvalidMemory', message: string }
    | { __typename: 'Memory', id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }
    | { __typename: 'MemoryNotFound', message: string }
    | { __typename: 'MemoryTooLong', message: string, length: number, limit: number }
   };


export const UpdateMemoryDocument = gql`
    mutation UpdateMemory($id: ID!, $input: UpdateMemoryInput!) {
  updateMemory(id: $id, input: $input) {
    __typename
    ... on Memory {
      ...MemoryFields
    }
    ... on MemoryTooLong {
      message
      length
      limit
    }
    ... on InvalidMemory {
      message
    }
    ... on MemoryNotFound {
      message
    }
  }
}
    ${MemoryFieldsFragmentDoc}`;