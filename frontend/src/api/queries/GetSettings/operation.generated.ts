/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
export type GetSettingsQueryVariables = Exact<{
  detectedTimezone?: string | null | undefined;
}>;


export type GetSettingsQuery = { settings: { timezone: string, updatedAt: string, defaultReminderTime: string, popupsEnabled: boolean, emailEnabled: boolean } };


export const GetSettingsDocument = gql`
    query GetSettings($detectedTimezone: String) {
  settings(detectedTimezone: $detectedTimezone) {
    timezone
    updatedAt
    defaultReminderTime
    popupsEnabled
    emailEnabled
  }
}
    `;