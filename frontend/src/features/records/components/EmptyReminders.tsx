import { Bell } from "lucide-react";
import type { ReactElement } from "react";

import * as Styles from "./styles";

interface EmptyRemindersProps {
  onStartCapturing: () => void;
}

/** `RemindersEmpty`. */
const EmptyReminders = (props: EmptyRemindersProps): ReactElement => {
  const { onStartCapturing } = props;

  return (
    <div className={Styles.noticeCardStyles}>
      <div className={Styles.emptyIconStyles}>
        <Bell size={24} />
      </div>
      <div className={Styles.emptyTitleStyles}>No reminders yet</div>
      <div className={Styles.emptyBodyStyles}>
        Set one from Capture and it appears here, grouped by what needs attention.
      </div>
      <button type="button" className={Styles.noticeExampleStyles} onClick={onStartCapturing}>
        /remind Call Mom tomorrow at 7pm
      </button>
    </div>
  );
};

export default EmptyReminders;
