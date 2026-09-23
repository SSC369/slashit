/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
import * as Types from '../../../../types.generated';

import { gql } from '@apollo/client';
export type UpdateReminderSettingsInput = {
  defaultReminderTime?: string | null | undefined;
  emailEnabled?: boolean | null | undefined;
  popupsEnabled?: boolean | null | undefined;
};

export type UpdateReminderSettingsMutationVariables = Exact<{
  input: Types.UpdateReminderSettingsInput;
}>;


export type UpdateReminderSettingsMutation = { updateReminderSettings:
    | { __typename: 'InvalidReminderSettings', message: string, field: string }
    | { __typename: 'ReminderSettingsSaved', showBothOffWarning: boolean, settings: { timezone: string, defaultReminderTime: string, popupsEnabled: boolean, emailEnabled: boolean } }
   };


export const UpdateReminderSettingsDocument = gql`
    mutation UpdateReminderSettings($input: UpdateReminderSettingsInput!) {
  updateReminderSettings(input: $input) {
    __typename
    ... on ReminderSettingsSaved {
      showBothOffWarning
      settings {
        timezone
        defaultReminderTime
        popupsEnabled
        emailEnabled
      }
    }
    ... on InvalidReminderSettings {
      message
      field
    }
  }
}
    `;