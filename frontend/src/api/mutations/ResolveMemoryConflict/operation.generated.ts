/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { MemoryFieldsFragmentDoc } from '../../../fragments/MemoryFields.generated';
export type ConflictAnswer =
  | 'BOTH'
  | 'KEEP_NEW'
  | 'KEEP_OLD';

export type MemoryCategory =
  | 'LIFE'
  | 'PEOPLE'
  | 'PERSONAL'
  | 'PROFESSIONAL';

export type SecretKind =
  | 'CARD'
  | 'CREDENTIAL'
  | 'ID_NUMBER'
  | 'TAX_ID';

export type ResolveMemoryConflictMutationVariables = Exact<{
  pendingCaptureId: string | number;
  answer: Types.ConflictAnswer;
}>;


export type ResolveMemoryConflictMutation = { resolveMemoryConflict:
    | { __typename: 'MemoryDiscarded', message: string }
    | { __typename: 'MemorySaved', secretCaution: Types.SecretKind | null, memory: { id: string, text: string, category: Types.MemoryCategory | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string } }
    | { __typename: 'PendingCaptureNotFound', message: string }
   };


export const ResolveMemoryConflictDocument = gql`
    mutation ResolveMemoryConflict($pendingCaptureId: ID!, $answer: ConflictAnswer!) {
  resolveMemoryConflict(pendingCaptureId: $pendingCaptureId, answer: $answer) {
    __typename
    ... on MemorySaved {
      memory {
        ...MemoryFields
      }
      secretCaution
    }
    ... on MemoryDiscarded {
      message
    }
    ... on PendingCaptureNotFound {
      message
    }
  }
}
    ${MemoryFieldsFragmentDoc}`;