import { AlertTriangle, InfoIcon } from "lucide-react";
import type { ChangeEvent, ReactElement } from "react";

import InlineSpinner from "../../../components/InlineSpinner";
import Skeleton from "../../../components/Skeleton";
import Switch from "../../../design-system/components/Switch";
import { formatClockTime } from "../../../utils/formatReminder";
import * as Styles from "./styles";

export type ReminderSettingType = "DEFAULT_TIME" | "POPUPS" | "EMAIL";

interface ReminderSettingsSectionProps {
  isLoading: boolean;
  /** "HH:MM", 24-hour. */
  defaultReminderTime: string;
  popupsEnabled: boolean;
  emailEnabled: boolean;
  accountEmail: string | null;
  savingSetting: ReminderSettingType | null;
  failureMessage: string | null;
  timeErrorMessage: string | null;
  isBothOffWarningShown: boolean;
  onChangeDefaultTime: (localTime: string) => void;
  onTogglePopups: (isOn: boolean) => void;
  onToggleEmail: (isOn: boolean) => void;
}

const MINUTES_PER_STEP = 30;

/** Every half hour of the day, "00:00" to "23:30", plus the saved time when
 * it falls between steps, so the control never shows a time it cannot hold. */
const listTimeChoices = (savedTime: string): string[] => {
  const choices: string[] = [];
  for (let minutes = 0; minutes < 24 * 60; minutes += MINUTES_PER_STEP) {
    const hour = String(Math.floor(minutes / 60)).padStart(2, "0");
    const minute = String(minutes % 60).padStart(2, "0");
    choices.push(`${hour}:${minute}`);
  }
  if (!choices.includes(savedTime)) choices.push(savedTime);
  return choices.sort();
};

const LoadingRows = (): ReactElement => (
  <div className={Styles.cardStyles} data-testid="reminder-settings-loading">
    {[0, 1, 2].map((row) => (
      <div key={row} className={Styles.rowStyles}>
        <div className={Styles.skeletonTextStyles}>
          <Skeleton width="30%" height={13} />
          <Skeleton width="55%" height={10} />
        </div>
        <Skeleton width="40px" height={23} className="rounded-full" />
      </div>
    ))}
  </div>
);

/**
 * `SettingsReminders` and its states: `SettingsLoading`, `SettingsSaving`,
 * `SettingsFailed` and `SettingsBothOff` (FR-31 to FR-34).
 */
const ReminderSettingsSection = (props: ReminderSettingsSectionProps): ReactElement => {
  const {
    isLoading,
    defaultReminderTime,
    popupsEnabled,
    emailEnabled,
    accountEmail,
    savingSetting,
    failureMessage,
    timeErrorMessage,
    isBothOffWarningShown,
    onChangeDefaultTime,
    onTogglePopups,
    onToggleEmail,
  } = props;

  const renderSpinner = (setting: ReminderSettingType): ReactElement | null =>
    savingSetting === setting ? <InlineSpinner className="text-foreground-secondary" /> : null;

  return (
    <div className={Styles.sectionStyles}>
      <div className="text-[16px] font-semibold text-foreground">Reminders</div>
      <div className="mt-1 text-[13.5px] text-foreground-secondary">
        How and when reminders reach you.
      </div>
      {isLoading ? (
        <LoadingRows />
      ) : (
        <div className={Styles.cardStyles}>
          <div className={Styles.rowStyles}>
            <div className={Styles.rowTextStyles}>
              <div className={Styles.rowTitleStyles}>Default reminder time</div>
              <div className={Styles.rowHintStyles}>
                Used when you give a date but no time, and for &ldquo;Snooze until tomorrow&rdquo;
              </div>
            </div>
            <div className={Styles.rowControlStyles}>
              {renderSpinner("DEFAULT_TIME")}
              <select
                aria-label="Default reminder time"
                className={Styles.timeSelectStyles}
                value={defaultReminderTime}
                disabled={savingSetting === "DEFAULT_TIME"}
                onChange={(event: ChangeEvent<HTMLSelectElement>) =>
                  onChangeDefaultTime(event.target.value)
                }
              >
                {listTimeChoices(defaultReminderTime).map((localTime) => (
                  <option key={localTime} value={localTime}>
                    {formatClockTime(localTime)}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {timeErrorMessage !== null && (
            <div className={Styles.fieldErrorStyles} role="alert">
              {timeErrorMessage}
            </div>
          )}
          <div className={Styles.rowStyles}>
            <div className={Styles.rowTextStyles}>
              <div className={Styles.rowTitleStyles}>Pop-ups in the app</div>
              <div className={Styles.rowHintStyles}>
                A card in the corner when a reminder fires while Slashit is open
              </div>
            </div>
            <div className={Styles.rowControlStyles}>
              {renderSpinner("POPUPS")}
              <Switch
                label="Pop-ups in the app"
                isOn={popupsEnabled}
                isBusy={savingSetting === "POPUPS"}
                onToggle={onTogglePopups}
              />
            </div>
          </div>
          <div className={Styles.rowStyles}>
            <div className={Styles.rowTextStyles}>
              <div className={Styles.rowTitleStyles}>Email</div>
              <div className={Styles.rowHintStyles}>
                {accountEmail !== null ? (
                  <>
                    Sent to <span className={Styles.rowEmailStyles}>{accountEmail}</span>, at most
                    50 a day
                  </>
                ) : (
                  "Sent to your account email, at most 50 a day"
                )}
              </div>
            </div>
            <div className={Styles.rowControlStyles}>
              {renderSpinner("EMAIL")}
              <Switch
                label="Email"
                isOn={emailEnabled}
                isBusy={savingSetting === "EMAIL"}
                onToggle={onToggleEmail}
              />
            </div>
          </div>
          {isBothOffWarningShown && (
            <div className={Styles.warnNoteStyles} role="status">
              <AlertTriangle size={17} className="shrink-0 text-command" />
              <div>
                <div className={Styles.warnTitleStyles}>Nothing will reach you outside Slashit.</div>
                <div className={Styles.warnBodyStyles}>
                  With both off, reminders only land in your notification list. You will not get a
                  pop-up or an email.
                </div>
              </div>
            </div>
          )}
          {failureMessage !== null && (
            <div className={Styles.errorNoteStyles} role="alert">
              <InfoIcon size={16} className="shrink-0 text-destructive" />
              <div>{failureMessage}</div>
            </div>
          )}
          <div className={Styles.cardFootStyles}>
            Every reminder also lands in your notification list, whatever these switches say.
          </div>
        </div>
      )}
    </div>
  );
};

export default ReminderSettingsSection;
