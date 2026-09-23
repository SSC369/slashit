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

export type GetNotificationsQueryVariables = Exact<{
  cursor?: string | null | undefined;
}>;


export type GetNotificationsQuery = { notifications: { nextCursor: string | null, items: Array<{ id: string, kind: Types.NotificationKind, targetId: string | null, title: string, detail: string, marker: Types.NotificationMarker, occurredAt: string, createdAt: string, read: boolean, action: Types.NotificationAction | null, actedAt: string | null, showPopup: boolean }> } };


export const GetNotificationsDocument = gql`
    query GetNotifications($cursor: String) {
  notifications(cursor: $cursor) {
    items {
      ...NotificationFields
    }
    nextCursor
  }
}
    ${NotificationFieldsFragmentDoc}`;