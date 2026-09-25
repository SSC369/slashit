import { ArrowRight, Check, X } from "lucide-react";
import type { ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import Button from "../../../design-system/components/Button";
import type { NotificationFieldsFragment } from "../../../fragments/NotificationFields.generated";
import type { NotificationActionState } from "../../../stores/NotificationsStore";
import { cn } from "../../../utils/cn";
import { formatInstantClock, type SnoozeOptionType } from "../../../utils/formatNotification";
import SnoozeMenu from "./SnoozeMenu";
import * as Styles from "./styles";

interface ReminderPopupProps {
  notification: NotificationFieldsFragment;
  actionState: NotificationActionState | null;
  isOffline: boolean;
  defaultReminderTime: string | null;
  onDone: (notification: NotificationFieldsFragment) => void;
  onSnooze: (notification: NotificationFieldsFragment, option: SnoozeOptionType) => void;
  onOpen: (notification: NotificationFieldsFragment) => void;
  onClose: (notification: NotificationFieldsFragment) => void;
}

/**
 * The corner card (FR-13, `ReminderToast`): stays until acted on or closed,
 * never steals focus. Acting, failed and offline are `PopupActing`,
 * `PopupFailed` and `PopupOffline`.
 */
const ReminderPopup = (props: ReminderPopupProps): ReactElement => {
  const { notification, actionState, isOffline, defaultReminderTime, onDone, onSnooze, onOpen, onClose } =
    props;
  const isActing = actionState?.status === "ACTING";
  const hasFailed = actionState?.status === "FAILED";

  return (
    <div className={Styles.popupStyles}>
      <div className={Styles.popupHeadStyles}>
        <span>Reminder · {formatInstantClock(new Date(notification.occurredAt))}</span>
        {notification.detail && <span className={Styles.popupRepeatStyles}>{notification.detail}</span>}
        <button
          type="button"
          aria-label="Close reminder"
          className={Styles.popupCloseStyles}
          onClick={() => onClose(notification)}
        >
          <X size={15} />
        </button>
      </div>
      <div className={Styles.popupTitleStyles}>{notification.title}</div>
      <div className={Styles.popupActionsStyles}>
        <BusyButton
          size="sm"
          variant="primary"
          isBusy={isActing && actionState?.kind === "DONE"}
          busyLabel="Marking done"
          disabled={isOffline || isActing}
          onClick={() => onDone(notification)}
        >
          <Check size={13} /> Done
        </BusyButton>
        <SnoozeMenu
          placement="top-start"
          defaultReminderTime={defaultReminderTime}
          isBusy={isActing && actionState?.kind === "SNOOZE"}
          isDisabled={isOffline || isActing}
          onPick={(option) => onSnooze(notification, option)}
        />
        <Button size="sm" disabled={isActing} onClick={() => onOpen(notification)}>
          Open <ArrowRight size={13} />
        </Button>
      </div>
      {isOffline && (
        <div className={cn(Styles.popupMessageStyles, Styles.popupOfflineStyles)}>
          You're offline. Done and Snooze need a connection.
        </div>
      )}
      {hasFailed && !isOffline && (
        <div className={cn(Styles.popupMessageStyles, Styles.popupErrorStyles)} role="alert">
          That didn't save. The reminder is still open. Try again.
        </div>
      )}
    </div>
  );
};

export default ReminderPopup;
