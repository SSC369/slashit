import { AlertCircle, InfoIcon, Trash2 } from "lucide-react";
import type { ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import Button from "../../../design-system/components/Button";
import { cn } from "../../../utils/cn";
import { WEEKDAY_LABELS } from "../../../utils/formatReminder";
import {
  describeDraftSchedule,
  describeIntervalUnit,
  type ReminderDraft,
  type ReminderFieldErrors,
  type RepeatKindType,
} from "../../../utils/reminderDraft";
import * as Styles from "./styles";

export type EditBannerType = "NONE" | "FAILED" | "GONE";

const REPEAT_OPTIONS: { kind: RepeatKindType; label: string }[] = [
  { kind: "NONE", label: "Does not repeat" },
  { kind: "DAILY", label: "Daily" },
  { kind: "WEEKLY", label: "Weekly" },
  { kind: "MONTHLY", label: "Monthly" },
  { kind: "YEARLY", label: "Yearly" },
];

interface ReminderEditFormProps {
  draft: ReminderDraft;
  timezone: string;
  fieldErrors: ReminderFieldErrors;
  banner: EditBannerType;
  isSaving: boolean;
  isOffline: boolean;
  onChange: (patch: Partial<ReminderDraft>) => void;
  onSave: () => void;
  onCancel: () => void;
}

/** `ReminderEdit` and its states: invalid, past, saving, failed, gone.
 * An edit replaces the whole series (FR-28). */
const ReminderEditForm = (props: ReminderEditFormProps): ReactElement => {
  const { draft, timezone, fieldErrors, banner, isSaving, isOffline, onChange, onSave, onCancel } =
    props;

  const isGone = banner === "GONE";
  const isLocked = isSaving || isGone;
  const hasFieldErrors = Object.keys(fieldErrors).length > 0;
  const isSaveDisabled = hasFieldErrors || isGone || isOffline;

  const toggleWeekday = (day: number): void => {
    const hasDay = draft.repeatWeekdays.includes(day);
    onChange({
      repeatWeekdays: hasDay
        ? draft.repeatWeekdays.filter((weekday) => weekday !== day)
        : [...draft.repeatWeekdays, day].sort((left, right) => left - right),
    });
  };

  return (
    <div>
      {banner === "FAILED" && (
        <div className={Styles.bannerErrorStyles} role="alert">
          <AlertCircle size={18} className="shrink-0 text-destructive" />
          <div>
            <div className={Styles.bannerTitleStyles}>Couldn't save your changes</div>
            <div className={Styles.bannerBodyStyles}>
              Your edits are still here. Nothing changed on the reminder. Try again in a moment.
            </div>
          </div>
        </div>
      )}
      {isGone && (
        <div className={Styles.bannerWarnStyles} role="alert">
          <Trash2 size={18} className="shrink-0 text-command" />
          <div>
            <div className={Styles.bannerTitleStyles}>This reminder was deleted</div>
            <div className={Styles.bannerBodyStyles}>
              It was deleted from another tab or device while you were editing. Your edits can't
              be saved to it.
            </div>
          </div>
        </div>
      )}

      <div className={Styles.formRowStyles}>
        <label className={Styles.formLabelStyles} htmlFor="reminder-description">
          Reminder
        </label>
        <div className={cn(Styles.controlStyles, fieldErrors.description && Styles.controlErrorStyles)}>
          <input
            id="reminder-description"
            className={Styles.controlInputStyles}
            type="text"
            placeholder="What should Slashit remind you about?"
            value={draft.description}
            disabled={isLocked}
            onChange={(event) => onChange({ description: event.target.value })}
          />
        </div>
        {fieldErrors.description && (
          <span className={Styles.fieldErrorStyles}>{fieldErrors.description}</span>
        )}
      </div>

      <div className={Styles.formGridStyles}>
        <div className={Styles.formRowStyles}>
          <label className={Styles.formLabelStyles} htmlFor="reminder-start">
            Starts
          </label>
          <div className={Styles.controlStyles}>
            <input
              id="reminder-start"
              className={Styles.controlNativeInputStyles}
              type="date"
              value={draft.startDate}
              disabled={isLocked}
              onChange={(event) => onChange({ startDate: event.target.value })}
            />
          </div>
        </div>
        <div className={Styles.formRowStyles}>
          <label className={Styles.formLabelStyles} htmlFor="reminder-time">
            Time
          </label>
          <div className={cn(Styles.controlStyles, fieldErrors.localTime && Styles.controlErrorStyles)}>
            <input
              id="reminder-time"
              className={Styles.controlNativeInputStyles}
              type="time"
              value={draft.localTime}
              disabled={isLocked}
              onChange={(event) => onChange({ localTime: event.target.value })}
            />
          </div>
          {fieldErrors.localTime && (
            <span className={Styles.fieldErrorStyles}>{fieldErrors.localTime}</span>
          )}
        </div>
      </div>

      <div className={Styles.formRowStyles}>
        <span className={Styles.formLabelStyles}>Repeat</span>
        <div className={cn(Styles.segStyles, isLocked && "pointer-events-none opacity-60")}>
          {REPEAT_OPTIONS.map((option) => (
            <button
              key={option.kind}
              type="button"
              aria-pressed={draft.repeatKind === option.kind}
              className={cn(
                Styles.segOptionStyles,
                draft.repeatKind === option.kind && Styles.segOptionOnStyles,
              )}
              disabled={isLocked}
              onClick={() => onChange({ repeatKind: option.kind })}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {draft.repeatKind !== "NONE" && (
        <div className={Styles.formRowStyles}>
          <label className={Styles.formLabelStyles} htmlFor="reminder-interval">
            Every
          </label>
          <div className={Styles.intervalRowStyles}>
            <input
              id="reminder-interval"
              className={Styles.intervalInputStyles}
              type="number"
              min={1}
              max={99}
              value={draft.repeatInterval}
              disabled={isLocked}
              onChange={(event) => onChange({ repeatInterval: Number(event.target.value) || 1 })}
            />
            <span className={Styles.controlReadOnlyStyles}>
              {describeIntervalUnit(draft.repeatKind, draft.repeatInterval)}
            </span>
          </div>
          {fieldErrors.repeatInterval && (
            <span className={Styles.fieldErrorStyles}>{fieldErrors.repeatInterval}</span>
          )}
        </div>
      )}

      {draft.repeatKind === "WEEKLY" && (
        <div className={Styles.formRowStyles}>
          <span className={Styles.formLabelStyles}>On</span>
          <div className={Styles.chipsStyles}>
            {WEEKDAY_LABELS.map((label, day) => {
              const isOn = draft.repeatWeekdays.includes(day);
              return (
                <button
                  key={label}
                  type="button"
                  aria-pressed={isOn}
                  className={cn(Styles.chipStyles, isOn && Styles.chipOnStyles)}
                  disabled={isLocked}
                  onClick={() => toggleWeekday(day)}
                >
                  {label}
                </button>
              );
            })}
          </div>
          {fieldErrors.repeatWeekdays && (
            <span className={Styles.fieldErrorStyles}>{fieldErrors.repeatWeekdays}</span>
          )}
        </div>
      )}

      <div className={Styles.noteInfoStyles}>
        <InfoIcon size={17} className="shrink-0 text-accent" />
        <div className={Styles.noteInfoTextStyles}>
          {describeDraftSchedule(draft, timezone)}
        </div>
      </div>

      <div className={Styles.formActionsRowStyles}>
        <BusyButton
          variant="primary"
          isBusy={isSaving}
          busyLabel="Saving"
          disabled={isSaveDisabled}
          onClick={onSave}
        >
          {banner === "FAILED" ? "Try again" : "Save changes"}
        </BusyButton>
        <Button onClick={onCancel} disabled={isSaving}>
          {isGone ? "Back to reminders" : "Cancel"}
        </Button>
      </div>
    </div>
  );
};

export default ReminderEditForm;
