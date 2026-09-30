/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
export type RecordSearchEventInput = {
  kind: SearchEventKind;
  position: number;
};

export type SearchEventKind =
  | 'ANSWER_CITATION_OPENED'
  | 'RELATED_OPENED'
  | 'SEARCH_RESULT_OPENED';

export type RecordSearchEventMutationVariables = Exact<{
  input: Types.RecordSearchEventInput;
}>;


export type RecordSearchEventMutation = { recordSearchEvent: boolean };


export const RecordSearchEventDocument = gql`
    mutation RecordSearchEvent($input: RecordSearchEventInput!) {
  recordSearchEvent(input: $input)
}
    `;