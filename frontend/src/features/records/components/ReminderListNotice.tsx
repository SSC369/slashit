import type { ReactElement } from "react";

import Button from "../../../design-system/components/Button";
import * as Styles from "./styles";

interface ReminderListNoticeProps {
  icon: ReactElement;
  title: string;
  body: string;
  actionLabel: string;
  onAction: () => void;
}

/** The Reminders tab's non-list states that offer one way forward:
 * `RemindersError`, `RemindersNoMatch`, `RemindersSessionEnded`. */
const ReminderListNotice = (props: ReminderListNoticeProps): ReactElement => {
  const { icon, title, body, actionLabel, onAction } = props;

  return (
    <div className={Styles.noticeCardStyles}>
      <div className={Styles.emptyIconStyles}>{icon}</div>
      <div className={Styles.emptyTitleStyles}>{title}</div>
      <div className={Styles.emptyBodyStyles}>{body}</div>
      <div className={Styles.emptyActionStyles}>
        <Button onClick={onAction}>{actionLabel}</Button>
      </div>
    </div>
  );
};

export default ReminderListNotice;
