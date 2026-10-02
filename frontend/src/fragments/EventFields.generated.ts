/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../types.generated';

import { gql } from '@apollo/client';
export type EventStatusType =
  | 'HAPPENING_NOW'
  | 'PAST'
  | 'UPCOMING';

export type EventFieldsFragment = { id: string, title: string, location: string | null, startDate: string, startTime: string | null, endDate: string | null, endTime: string | null, allDay: boolean, repeatYearly: boolean, scheduleTimezone: string, startsAt: string, endsAt: string, occurrenceDate: string, occurrenceEndDate: string, whenText: string, alertLeadMinutes: number | null, alertText: string | null, alertFiresAt: string | null, origin: string, originalInput: string | null, createdAt: string, updatedAt: string, whenNotes: Array<string>, eventDescription: string | null, eventStatus: Types.EventStatusType };

export const EventFieldsFragmentDoc = gql`
    fragment EventFields on Event {
  id
  title
  location
  eventDescription: description
  startDate
  startTime
  endDate
  endTime
  allDay
  repeatYearly
  scheduleTimezone
  startsAt
  endsAt
  occurrenceDate
  occurrenceEndDate
  eventStatus: status
  whenText
  alertLeadMinutes
  alertText
  alertFiresAt
  origin
  originalInput
  createdAt
  updatedAt
  whenNotes
}
    `;