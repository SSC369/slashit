import type { GetSettingsQuery } from "./operation.generated";

export interface GetSettingsCallbacks {
  onSettingsLoaded?: (args: {
    timezone: string;
    updatedAt: string;
    defaultReminderTime: string;
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
    });
  };

  return { handleResponse };
};
