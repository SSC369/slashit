import type { UpdateReminderSettingsMutation } from "./operation.generated";

export interface ReminderSettingsType {
  timezone: string;
  defaultReminderTime: string;
  popupsEnabled: boolean;
  emailEnabled: boolean;
}

export interface UpdateReminderSettingsCallbacks {
  onReminderSettingsSaved?: (args: {
    settings: ReminderSettingsType;
    showBothOffWarning: boolean;
  }) => void;
  onInvalidReminderSettings?: (args: { message: string; field: string }) => void;
}

interface UseResponseHandlerArgs extends UpdateReminderSettingsCallbacks {
  data: UpdateReminderSettingsMutation | null | undefined;
}

const assertNever = (value: never): never => {
  throw new Error(`Unhandled UpdateReminderSettingsResult type: ${JSON.stringify(value)}`);
};

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, ...callbacks } = args;
    if (!data?.updateReminderSettings) return;

    const result = data.updateReminderSettings;
    switch (result.__typename) {
      case "ReminderSettingsSaved":
        callbacks.onReminderSettingsSaved?.({
          settings: {
            timezone: result.settings.timezone,
            defaultReminderTime: result.settings.defaultReminderTime,
            popupsEnabled: result.settings.popupsEnabled,
            emailEnabled: result.settings.emailEnabled,
          },
          showBothOffWarning: result.showBothOffWarning,
        });
        return;
      case "InvalidReminderSettings":
        callbacks.onInvalidReminderSettings?.({ message: result.message, field: result.field });
        return;
      default:
        assertNever(result);
    }
  };

  return { handleResponse };
};
