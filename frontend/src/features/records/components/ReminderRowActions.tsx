import { Check } from "lucide-react";
import type { ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import type { NotificationActionState } from "../../../stores/NotificationsStore";
import type { SnoozeOptionType } from "../../../utils/formatNotification";
import SnoozeMenu from "../../notifications/components/SnoozeMenu";
import * as Styles from "./styles";

interface ReminderRowActionsProps {
  reminder: ReminderFieldsFragment;
  actionState: NotificationActionState | null;
  isOffline: boolean;
  defaultReminderTime: string | null;
  onDone: (reminder: ReminderFieldsFragment) => void;
  onSnooze: (reminder: ReminderFieldsFragment, option: SnoozeOptionType) => void;
}

/** `Main`: Done and Snooze beside a reminder that needs attention. Shared by
 * the Reminders tab row and the detail page. */
const ReminderRowActions = (props: ReminderRowActionsProps): ReactElement => {
  const { reminder, actionState, isOffline, defaultReminderTime, onDone, onSnooze } = props;
  const isActing = actionState?.status === "ACTING";

  return (
    <span className={Styles.rowActionsStyles} onClick={(event) => event.stopPropagation()}>
      <BusyButton
        size="sm"
        isBusy={isActing && actionState?.kind === "DONE"}
        busyLabel="Marking done"
        disabled={isOffline || isActing}
        onClick={() => onDone(reminder)}
      >
        <Check size={13} /> Done
      </BusyButton>
      <SnoozeMenu
        placement="bottom-start"
        defaultReminderTime={defaultReminderTime}
        isBusy={isActing && actionState?.kind === "SNOOZE"}
        isDisabled={isOffline || isActing}
        onPick={(option) => onSnooze(reminder, option)}
      />
      {actionState?.status === "FAILED" && (
        <span className={Styles.rowActionErrorStyles} role="alert">
          That didn't save. Try again.
        </span>
      )}
    </span>
  );
};

export default ReminderRowActions;
