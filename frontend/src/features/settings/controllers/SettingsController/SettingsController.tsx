import { InfoIcon } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useMemo, useState, type ChangeEvent, type ReactElement } from "react";

import useUpdateReminderSettings from "../../../../api/mutations/UpdateReminderSettings/useUpdateReminderSettings";
import useUpdateTimezone from "../../../../api/mutations/UpdateTimezone/useUpdateTimezone";
import useGetSettings from "../../../../api/queries/GetSettings/useGetSettings";
import { useResponseHandler } from "../../../../api/queries/GetSettings/responseHandler";
import Button from "../../../../design-system/components/Button";
import { useStore } from "../../../../stores/StoreProvider";
import { cn } from "../../../../utils/cn";
import { detectTimezone } from "../../../../utils/detectTimezone";
import { formatClockTime } from "../../../../utils/formatReminder";
import PageTopbar from "../../../../components/PageTopbar";
import {
  getThemePreference,
  setThemePreference,
  type ThemePreferenceType,
} from "../../../../utils/themePreference";
import ReminderSettingsSection, {
  type ReminderSettingType,
} from "../../components/ReminderSettingsSection";
import * as Styles from "./styles";

interface ThemeOptionProps {
  value: ThemePreferenceType;
  label: string;
}

const THEME_OPTIONS: ThemeOptionProps[] = [
  { value: "SYSTEM", label: "System" },
  { value: "LIGHT", label: "Light" },
  { value: "DARK", label: "Dark" },
];

const listSupportedTimezones = (): string[] => {
  try {
    return Intl.supportedValuesOf("timeZone");
  } catch {
    return [];
  }
};

const FALLBACK_REMINDER_TIME = "09:00";

/** `SettingsFailed`: what did not change, and that the old value still holds. */
const describeSaveFailure = (args: {
  setting: ReminderSettingType;
  isOn: boolean;
  previousTime: string;
}): string => {
  const { setting, isOn, previousTime } = args;
  const wanted = isOn ? "on" : "off";
  const kept = isOn ? "off" : "on";
  switch (setting) {
    case "EMAIL":
      return `Couldn't turn email ${wanted}. It is still ${kept}. Try again.`;
    case "POPUPS":
      return `Couldn't turn pop-ups ${wanted}. They are still ${kept}. Try again.`;
    case "DEFAULT_TIME":
      return `Couldn't change the default time. It is still ${formatClockTime(previousTime)}. Try again.`;
  }
};

const SettingsController = (): ReactElement => {
  const store = useStore();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [themePreference, setThemePreferenceValue] = useState<ThemePreferenceType>(
    getThemePreference,
  );
  const timezones = useMemo(listSupportedTimezones, []);

  const { triggerAPI: triggerGetSettings, data } = useGetSettings();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: triggerUpdateTimezone } = useUpdateTimezone();
  const { triggerAPI: triggerUpdateReminderSettings } = useUpdateReminderSettings();
  const [savingSetting, setSavingSetting] = useState<ReminderSettingType | null>(null);
  const [reminderFailureMessage, setReminderFailureMessage] = useState<string | null>(null);
  const [timeErrorMessage, setTimeErrorMessage] = useState<string | null>(null);
  const [isBothOffWarningShown, setIsBothOffWarningShown] = useState(false);

  useEffect(() => {
    triggerGetSettings({ detectedTimezone: detectTimezone() });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!data) return;
    handleResponse({
      data,
      onSettingsLoaded: (settings) => store.settings.setSettings(settings),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const handleTimezoneChange = (event: ChangeEvent<HTMLSelectElement>): void => {
    const timezone = event.target.value;
    triggerUpdateTimezone({
      timezone,
      onTimezoneUpdated: (updated) => {
        store.settings.setSettings(updated);
        setErrorMessage(null);
      },
      onInvalidTimezone: (message) => setErrorMessage(message),
    });
  };

  /** The control shows the new value at once and flips back if the save
   * fails (`SettingsSaving`, `SettingsFailed`). */
  const saveReminderSetting = (args: {
    setting: ReminderSettingType;
    input: { defaultReminderTime?: string; popupsEnabled?: boolean; emailEnabled?: boolean };
    isOn: boolean;
  }): void => {
    const { setting, input, isOn } = args;
    const settings = store.settings;
    const previous = {
      timezone: settings.timezone ?? "",
      defaultReminderTime: settings.defaultReminderTime ?? FALLBACK_REMINDER_TIME,
      popupsEnabled: settings.popupsEnabled,
      emailEnabled: settings.emailEnabled,
    };
    settings.setSettings({ ...previous, ...input });
    setSavingSetting(setting);
    setReminderFailureMessage(null);
    setTimeErrorMessage(null);
    triggerUpdateReminderSettings({
      input,
      onReminderSettingsSaved: ({ settings: saved, showBothOffWarning }) => {
        settings.setSettings(saved);
        setSavingSetting(null);
        if (showBothOffWarning) setIsBothOffWarningShown(true);
        if (saved.popupsEnabled || saved.emailEnabled) setIsBothOffWarningShown(false);
      },
      onInvalidReminderSettings: ({ message }) => {
        settings.setSettings(previous);
        setSavingSetting(null);
        setTimeErrorMessage(message);
      },
      onRequestFailed: () => {
        settings.setSettings(previous);
        setSavingSetting(null);
        setReminderFailureMessage(
          describeSaveFailure({ setting, isOn, previousTime: previous.defaultReminderTime }),
        );
      },
    });
  };

  const handleThemePreferenceChange = (preference: ThemePreferenceType): void => {
    setThemePreference(preference);
    setThemePreferenceValue(preference);
  };

  return (
    <div className={Styles.pageStyles}>
      <PageTopbar title="Settings" />
      <div className={Styles.paneStyles}>
        <div className={Styles.contentStyles}>
          <div className={Styles.sectionTitleStyles}>Timezone</div>
          <div className={Styles.sectionBodyStyles}>
            Slashit resolves &ldquo;tomorrow&rdquo; and &ldquo;7pm&rdquo; against this.
          </div>
          <div className={Styles.controlWrapStyles}>
            <div className={Styles.formRowStyles}>
              <span className={Styles.formLabelStyles}>Timezone</span>
              <select
                className={Styles.selectControlStyles}
                value={store.settings.timezone ?? ""}
                onChange={handleTimezoneChange}
              >
                {store.settings.timezone && !timezones.includes(store.settings.timezone) && (
                  <option value={store.settings.timezone}>{store.settings.timezone}</option>
                )}
                {timezones.map((timezone) => (
                  <option key={timezone} value={timezone}>
                    {timezone}
                  </option>
                ))}
              </select>
            </div>
            {errorMessage ? (
              <div className={Styles.noteErrorStyles}>
                <InfoIcon size={17} className="shrink-0 text-destructive" />
                <div className={Styles.noteInfoTextStyles}>{errorMessage}</div>
              </div>
            ) : (
              <div className={Styles.noteInfoStyles}>
                <InfoIcon size={17} className="shrink-0 text-accent" />
                <div className={Styles.noteInfoTextStyles}>
                  Detected from your browser. Changing it affects how Slashit reads dates from
                  here on. Dates already recorded stay exactly as they are.
                </div>
              </div>
            )}
          </div>

          <ReminderSettingsSection
            isLoading={store.settings.timezone === null}
            defaultReminderTime={store.settings.defaultReminderTime ?? FALLBACK_REMINDER_TIME}
            popupsEnabled={store.settings.popupsEnabled}
            emailEnabled={store.settings.emailEnabled}
            accountEmail={store.auth.email}
            savingSetting={savingSetting}
            failureMessage={reminderFailureMessage}
            timeErrorMessage={timeErrorMessage}
            isBothOffWarningShown={isBothOffWarningShown}
            onChangeDefaultTime={(localTime) =>
              saveReminderSetting({
                setting: "DEFAULT_TIME",
                input: { defaultReminderTime: localTime },
                isOn: true,
              })
            }
            onTogglePopups={(isOn) =>
              saveReminderSetting({ setting: "POPUPS", input: { popupsEnabled: isOn }, isOn })
            }
            onToggleEmail={(isOn) =>
              saveReminderSetting({ setting: "EMAIL", input: { emailEnabled: isOn }, isOn })
            }
          />

          <div className={Styles.sectionStyles}>
            <div className={Styles.sectionTitleStyles}>Appearance</div>
            <div className={Styles.sectionBodyStyles}>
              Follows your system by default, or pick a theme.
            </div>
            <div className={Styles.controlWrapStyles}>
              <div className={Styles.formRowStyles}>
                <span className={Styles.formLabelStyles}>Theme</span>
                <div className={Styles.themeOptionGroupStyles} role="group" aria-label="Theme">
                  {THEME_OPTIONS.map((option) => {
                    const isSelected = themePreference === option.value;
                    return (
                      <Button
                        key={option.value}
                        type="button"
                        variant="default"
                        aria-pressed={isSelected}
                        className={cn(
                          Styles.themeOptionButtonStyles,
                          isSelected && Styles.themeOptionOnStyles,
                        )}
                        onClick={() => handleThemePreferenceChange(option.value)}
                      >
                        {option.label}
                      </Button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default observer(SettingsController);
