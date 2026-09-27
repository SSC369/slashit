/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { MemoryFieldsFragmentDoc } from '../../../fragments/MemoryFields.generated';
export type MemoriesFilterInput = {
  category?: MemoryCategory | null | undefined;
  search?: string | null | undefined;
  uncategorised?: boolean;
};

export type MemoryCategory =
  | 'LIFE'
  | 'PEOPLE'
  | 'PERSONAL'
  | 'PROFESSIONAL';

export type GetMemoriesQueryVariables = Exact<{
  filter?: Types.MemoriesFilterInput | null | undefined;
}>;


export type GetMemoriesQuery = { memories: Array<{ id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string }> };


export const GetMemoriesDocument = gql`
    query GetMemories($filter: MemoriesFilterInput) {
  memories(filter: $filter) {
    ...MemoryFields
  }
}
    ${MemoryFieldsFragmentDoc}`;