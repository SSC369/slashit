/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../types.generated';

import { gql } from '@apollo/client';
export type CaptureTurnOutcome =
  | 'DISCARDED'
  | 'MEMORY_LISTED'
  | 'MEMORY_SAVED'
  | 'QUESTION_ASKED'
  | 'REFUSED'
  | 'REMINDER_CREATED'
  | 'TASK_CREATED';

export type CaptureTurnFieldsFragment = { id: string, inputText: string, outcome: Types.CaptureTurnOutcome, resultingTaskId: string | null, resultingPendingCaptureId: string | null, resultingMemoryId: string | null, questionText: string | null, answerText: string | null, createdAt: string };

export const CaptureTurnFieldsFragmentDoc = gql`
    fragment CaptureTurnFields on CaptureTurn {
  id
  inputText
  outcome
  resultingTaskId
  resultingPendingCaptureId
  resultingMemoryId
  questionText
  answerText
  createdAt
}
    `;