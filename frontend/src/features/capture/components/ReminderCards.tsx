import { ArrowRight, Check, Pencil } from "lucide-react";
import type { ReactElement } from "react";
import { Link } from "react-router";

import ReminderStatusPill from "../../../components/ReminderStatusPill";
import Button from "../../../design-system/components/Button";
import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import { describeRepeatDetail, formatReminderDate } from "../../../utils/formatReminder";
import * as Styles from "./styles";

/** The server's note when no time was typed (FR-3); the card then offers the
 * setting that chose the time. */
const DEFAULT_TIME_NOTE = "No time given, so your default reminder time";

interface ReminderCreatedCardProps {
  reminder: ReminderFieldsFragment;
  onEditReminder: (id: string) => void;
  onOpenReminder: (id: string) => void;
}

/** `RemindCapture` and `RemindResolved`: the reminder as the server
 * understood it, with the reason when its time is not what was typed. */
export const ReminderCreatedCard = (props: ReminderCreatedCardProps): ReactElement => {
  const { reminder, onEditReminder, onOpenReminder } = props;
  const isRepeating = reminder.repeatKind !== "NONE";
  const repeatDetail = describeRepeatDetail(reminder);

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillDoneStyles}`}>
          <Check size={13} /> Reminder set
        </span>
      </div>
      <div className={Styles.fieldsGridStyles}>
        <div className={Styles.fieldCellStyles}>
          <span className={Styles.fieldLabelStyles}>Reminder</span>
          <span className={Styles.fieldValueStyles}>{reminder.description}</span>
        </div>
        <div className={Styles.fieldCellStyles}>
          <span className={Styles.fieldLabelStyles}>{isRepeating ? "Next" : "When"}</span>
          <span className={Styles.fieldValueStyles}>{reminder.whenText}</span>
          {reminder.whenNote !== null ? (
            <span className={Styles.fieldNoteStyles}>{reminder.whenNote}</span>
          ) : (
            reminder.nextFireAt !== null && (
              <span className={Styles.fieldSubStyles}>
                {formatReminderDate(reminder.nextFireAt, reminder.scheduleTimezone)}
              </span>
            )
          )}
        </div>
        <div className={Styles.fieldCellStyles}>
          <span className={Styles.fieldLabelStyles}>Repeat</span>
          <span className={Styles.fieldValueStyles}>{reminder.repeatText}</span>
          {repeatDetail !== null && <span className={Styles.fieldSubStyles}>{repeatDetail}</span>}
        </div>
      </div>
      <div className={Styles.cardFootStyles}>
        <span>
          Created just now · via command
          {reminder.whenNote === DEFAULT_TIME_NOTE && (
            <>
              {" · "}
              <Link to="/settings" className={Styles.footLinkStyles}>
                Change default time
              </Link>
            </>
          )}
        </span>
        <div className={Styles.cardFootActionsStyles}>
          <Button size="sm" onClick={() => onEditReminder(reminder.id)}>
            <Pencil size={13} /> Edit
          </Button>
          <Button size="sm" onClick={() => onOpenReminder(reminder.id)}>
            Open in Records <ArrowRight size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
};

interface ReminderListCardProps {
  reminders: ReminderFieldsFragment[];
  onOpenReminder: (id: string) => void;
  onOpenReminders: () => void;
}

/** `RemindList`: what `/reminders` returned, soonest first. */
export const ReminderListCard = (props: ReminderListCardProps): ReactElement => {
  const { reminders, onOpenReminder, onOpenReminders } = props;
  const countLabel = `${reminders.length} active ${reminders.length === 1 ? "reminder" : "reminders"}`;

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={Styles.reminderListHeadStyles}>
          {reminders.length > 0 ? `${countLabel} · soonest first` : "No active reminders"}
        </span>
      </div>
      {reminders.length > 0 ? (
        <div>
          {reminders.map((reminder) => (
            <div
              key={reminder.id}
              className={Styles.reminderListRowStyles}
              onClick={() => onOpenReminder(reminder.id)}
            >
              <span className={Styles.reminderListNameStyles}>{reminder.description}</span>
              <span className={Styles.reminderListMetaStyles}>{reminder.whenText}</span>
              <span className={Styles.reminderListMetaStyles}>{reminder.repeatText}</span>
              <span>
                <ReminderStatusPill reminder={reminder} />
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className={Styles.taskListRowStyles}>
          <span className={Styles.reminderListMetaStyles}>
            Set one with /remind, for example “/remind Call Mom tomorrow at 7pm”.
          </span>
        </div>
      )}
      <div className={Styles.cardFootStyles}>
        <span>From /reminders</span>
        <Button size="sm" onClick={onOpenReminders}>
          Open in Records <ArrowRight size={14} />
        </Button>
      </div>
    </div>
  );
};
