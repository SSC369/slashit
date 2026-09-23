import { InfoIcon } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useMemo, useState, type ChangeEvent, type ReactElement } from "react";

import useUpdateTimezone from "../../../../api/mutations/UpdateTimezone/useUpdateTimezone";
import useGetSettings from "../../../../api/queries/GetSettings/useGetSettings";
import { useResponseHandler } from "../../../../api/queries/GetSettings/responseHandler";
import Button from "../../../../design-system/components/Button";
import { useStore } from "../../../../stores/StoreProvider";
import { cn } from "../../../../utils/cn";
import { detectTimezone } from "../../../../utils/detectTimezone";
import PageTopbar from "../../../../components/PageTopbar";
import {
  getThemePreference,
  setThemePreference,
  type ThemePreferenceType,
} from "../../../../utils/themePreference";
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
