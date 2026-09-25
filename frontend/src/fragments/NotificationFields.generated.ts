/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../types.generated';

import { gql } from '@apollo/client';
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

export type NotificationFieldsFragment = { id: string, kind: Types.NotificationKind, targetId: string | null, title: string, detail: string, marker: Types.NotificationMarker, occurredAt: string, createdAt: string, read: boolean, action: Types.NotificationAction | null, actedAt: string | null, showPopup: boolean };

export const NotificationFieldsFragmentDoc = gql`
    fragment NotificationFields on Notification {
  id
  kind
  targetId
  title
  detail
  marker
  occurredAt
  createdAt
  read
  action
  actedAt
  showPopup
}
    `;