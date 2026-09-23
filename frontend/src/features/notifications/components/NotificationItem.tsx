import { ArrowRight, Check } from "lucide-react";
import type { ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import Button from "../../../design-system/components/Button";
import type { NotificationFieldsFragment } from "../../../fragments/NotificationFields.generated";
import type { NotificationActionState } from "../../../stores/NotificationsStore";
import { cn } from "../../../utils/cn";
import { describeNotificationMeta, type SnoozeOptionType } from "../../../utils/formatNotification";
import SnoozeMenu from "./SnoozeMenu";
import * as Styles from "./styles";

interface NotificationItemProps {
  notification: NotificationFieldsFragment;
  actionState: NotificationActionState | null;
  isOffline: boolean;
  defaultReminderTime: string | null;
  onOpen: (notification: NotificationFieldsFragment) => void;
  onDone: (notification: NotificationFieldsFragment) => void;
  onSnooze: (notification: NotificationFieldsFragment, option: SnoozeOptionType) => void;
}

const FAILURE_COPY: Record<NotificationActionState["kind"], string> = {
  DONE: "Couldn't mark it done. Try again.",
  SNOOZE: "Couldn't snooze it. Try again.",
};

/** One row of the panel: unread dot, Late or Missed marker, and, until acted
 * on, Done, Snooze and Open (`NotificationPanel`, `PanelActionFailed`). */
const NotificationItem = (props: NotificationItemProps): ReactElement => {
  const { notification, actionState, isOffline, defaultReminderTime, onOpen, onDone, onSnooze } =
    props;
  const isReminder = notification.kind === "REMINDER" && notification.targetId !== null;
  const isAwaitingAction = isReminder && notification.action === null;
  const isActing = actionState?.status === "ACTING";
  const hasFailed = actionState?.status === "FAILED";

  return (
    <div className={cn(Styles.itemStyles, !notification.read && Styles.itemUnreadStyles)}>
      {!notification.read && <span className={Styles.itemUnreadDotStyles} aria-label="Unread" />}
      <div className={Styles.itemTitleRowStyles}>
        <span className={Styles.itemTitleStyles}>{notification.title}</span>
        {notification.marker === "LATE" && (
          <span className={cn(Styles.markerBaseStyles, Styles.markerLateStyles)}>Late</span>
        )}
        {notification.marker === "MISSED" && (
          <span className={cn(Styles.markerBaseStyles, Styles.markerMissedStyles)}>Missed</span>
        )}
      </div>
      <div className={Styles.itemMetaStyles}>{describeNotificationMeta(notification, new Date())}</div>
      {isReminder && (
        <div className={Styles.itemActionsStyles}>
          {isAwaitingAction && (
            <>
              <BusyButton
                size="sm"
                isBusy={isActing && actionState?.kind === "DONE"}
                busyLabel="Marking done"
                disabled={isOffline || isActing}
                onClick={() => onDone(notification)}
              >
                <Check size={13} /> Done
              </BusyButton>
              <SnoozeMenu
                placement="bottom-start"
                defaultReminderTime={defaultReminderTime}
                isBusy={isActing && actionState?.kind === "SNOOZE"}
                isDisabled={isOffline || isActing}
                onPick={(option) => onSnooze(notification, option)}
              />
            </>
          )}
          <Button size="sm" onClick={() => onOpen(notification)}>
            Open <ArrowRight size={13} />
          </Button>
        </div>
      )}
      {hasFailed && actionState !== null && (
        <div className={Styles.itemErrorStyles} role="alert">
          {FAILURE_COPY[actionState.kind]}
        </div>
      )}
    </div>
  );
};

export default NotificationItem;
