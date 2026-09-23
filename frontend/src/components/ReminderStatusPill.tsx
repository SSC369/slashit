import type { ReactElement } from "react";

import type { ReminderFieldsFragment } from "../fragments/ReminderFields.generated";
import { cn } from "../utils/cn";
import {
  REMINDER_STATUS_LABEL,
  reminderStatusTone,
  type ReminderStatusToneType,
} from "../utils/formatReminder";
import * as Styles from "./styles";

const TONE_STYLES: Record<ReminderStatusToneType, string> = {
  UPCOMING: Styles.statusPillUpcomingStyles,
  FIRED: Styles.statusPillFiredStyles,
  MISSED: Styles.statusPillMissedStyles,
  DONE: Styles.statusPillDoneStyles,
};

interface ReminderStatusPillProps {
  reminder: ReminderFieldsFragment;
}

export const ReminderStatusPill = (props: ReminderStatusPillProps): ReactElement => {
  const { reminder } = props;
  const tone = reminderStatusTone(reminder);
  return (
    <span className={cn(Styles.statusPillBaseStyles, TONE_STYLES[tone])}>
      {REMINDER_STATUS_LABEL[tone]}
    </span>
  );
};

export default ReminderStatusPill;
