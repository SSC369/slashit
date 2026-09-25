/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { CaptureTurnFieldsFragmentDoc } from '../../../fragments/CaptureTurnFields.generated';
export type CaptureTurnOutcome =
  | 'DISCARDED'
  | 'MEMORY_LISTED'
  | 'MEMORY_SAVED'
  | 'QUESTION_ASKED'
  | 'REFUSED'
  | 'REMINDER_CREATED'
  | 'TASK_CREATED';

export type GetCaptureHistoryQueryVariables = Exact<{
  cursor?: string | null | undefined;
}>;


export type GetCaptureHistoryQuery = { captureHistory: { nextCursor: string | null, items: Array<{ id: string, inputText: string, outcome: Types.CaptureTurnOutcome, resultingTaskId: string | null, resultingPendingCaptureId: string | null, resultingMemoryId: string | null, questionText: string | null, answerText: string | null, createdAt: string }> } };


export const GetCaptureHistoryDocument = gql`
    query GetCaptureHistory($cursor: String) {
  captureHistory(cursor: $cursor) {
    nextCursor
    items {
      ...CaptureTurnFields
    }
  }
}
    ${CaptureTurnFieldsFragmentDoc}`;