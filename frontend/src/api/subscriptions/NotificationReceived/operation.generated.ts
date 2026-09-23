/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
import { NotificationFieldsFragmentDoc } from '../../../fragments/NotificationFields.generated';
export type NotificationAction =
  | 'DONE'
  | 'SNOOZED';

export type NotificationKind =
  | 'EMAIL_PAUSED'
  | 'REMINDER';

export type NotificationMarker =
  | 'LATE'
  | 'MISSED'
  | 'NONE';

export type NotificationReceivedSubscriptionVariables = Exact<{ [key: string]: never; }>;


export type NotificationReceivedSubscription = { notificationReceived: { id: string, kind: Types.NotificationKind, targetId: string | null, title: string, detail: string, marker: Types.NotificationMarker, occurredAt: string, createdAt: string, read: boolean, action: Types.NotificationAction | null, actedAt: string | null, showPopup: boolean } };


export const NotificationReceivedDocument = gql`
    subscription NotificationReceived {
  notificationReceived {
    ...NotificationFields
  }
}
    ${NotificationFieldsFragmentDoc}`;