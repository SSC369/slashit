/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { EventFieldsFragmentDoc } from '../../../fragments/EventFields.generated';
export type EventStatusType =
  | 'HAPPENING_NOW'
  | 'PAST'
  | 'UPCOMING';

export type GetEventQueryVariables = Exact<{
  id: string | number;
}>;


export type GetEventQuery = { event:
    | { __typename: 'Event', id: string, title: string, location: string | null, startDate: string, startTime: string | null, endDate: string | null, endTime: string | null, allDay: boolean, repeatYearly: boolean, scheduleTimezone: string, startsAt: string, endsAt: string, occurrenceDate: string, occurrenceEndDate: string, whenText: string, alertLeadMinutes: number | null, alertText: string | null, alertFiresAt: string | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNotes: Array<string>, eventDescription: string | null, eventStatus: Types.EventStatusType }
    | { __typename: 'EventNotFound', message: string }
   };


export const GetEventDocument = gql`
    query GetEvent($id: ID!) {
  event(id: $id) {
    __typename
    ... on Event {
      ...EventFields
    }
    ... on EventNotFound {
      message
    }
  }
}
    ${EventFieldsFragmentDoc}`;