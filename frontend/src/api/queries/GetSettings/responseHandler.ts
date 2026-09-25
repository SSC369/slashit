import type { GetSettingsQuery } from "./operation.generated";

export interface GetSettingsCallbacks {
  onSettingsLoaded?: (args: {
    timezone: string;
    updatedAt: string;
    defaultReminderTime: string;
    popupsEnabled: boolean;
    emailEnabled: boolean;
  }) => void;
}

interface UseResponseHandlerArgs extends GetSettingsCallbacks {
  data: GetSettingsQuery | null | undefined;
}

export const useResponseHandler = (): {
  handleResponse: (args: UseResponseHandlerArgs) => void;
} => {
  const handleResponse = (args: UseResponseHandlerArgs): void => {
    const { data, onSettingsLoaded } = args;
    if (!data?.settings) return;
    onSettingsLoaded?.({
      timezone: data.settings.timezone,
      updatedAt: data.settings.updatedAt,
      defaultReminderTime: data.settings.defaultReminderTime,
      popupsEnabled: data.settings.popupsEnabled,
      emailEnabled: data.settings.emailEnabled,
    });
  };

  return { handleResponse };
};
