import { AlertCircle, Bell, X } from "lucide-react";
import { useEffect, type ReactElement } from "react";

import Skeleton from "../../../components/Skeleton";
import Button from "../../../design-system/components/Button";
import type { NotificationFieldsFragment } from "../../../fragments/NotificationFields.generated";
import type { NotificationActionState } from "../../../stores/NotificationsStore";
import type { SnoozeOptionType } from "../../../utils/formatNotification";
import NotificationItem from "./NotificationItem";
import * as Styles from "./styles";

export type PanelStateType = "LOADING" | "ERROR" | "EMPTY" | "LIST";

interface NotificationPanelProps {
  panelState: PanelStateType;
  notifications: NotificationFieldsFragment[];
  unreadCount: number;
  hasMore: boolean;
  isLoadingMore: boolean;
  isOffline: boolean;
  defaultReminderTime: string | null;
  actionStates: Map<string, NotificationActionState>;
  onClose: () => void;
  onRetry: () => void;
  onLoadMore: () => void;
  onMarkAllRead: () => void;
  onOpen: (notification: NotificationFieldsFragment) => void;
  onDone: (notification: NotificationFieldsFragment) => void;
  onSnooze: (notification: NotificationFieldsFragment, option: SnoozeOptionType) => void;
}

const SKELETON_ITEM_COUNT = 4;

/** FR-35 to FR-37: the slide-over list, with every state of `NotificationStates`. */
const NotificationPanel = (props: NotificationPanelProps): ReactElement => {
  const {
    panelState,
    notifications,
    unreadCount,
    hasMore,
    isLoadingMore,
    isOffline,
    defaultReminderTime,
    actionStates,
    onClose,
    onRetry,
    onLoadMore,
    onMarkAllRead,
    onOpen,
    onDone,
    onSnooze,
  } = props;

  // Esc closes it (design §7); focus goes back to the bell with the page.
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
    // onClose is a store action, stable by construction (repo-rules §13.4).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <div className={Styles.panelOverlayStyles} onClick={onClose} />
      <aside className={Styles.panelStyles} aria-label="Notifications">
        <div className={Styles.panelHeadStyles}>
          <span className={Styles.panelTitleStyles}>Notifications</span>
          {unreadCount > 0 && <span className={Styles.panelUnreadStyles}>{unreadCount} unread</span>}
          <div className={Styles.panelHeadActionsStyles}>
            {unreadCount > 0 && (
              <button
                type="button"
                className={Styles.panelLinkButtonStyles}
                disabled={isOffline}
                onClick={onMarkAllRead}
              >
                Mark all read
              </button>
            )}
            <button
              type="button"
              aria-label="Close notifications"
              className={Styles.panelCloseStyles}
              onClick={onClose}
            >
              <X size={16} />
            </button>
          </div>
        </div>

        <div className={Styles.panelBodyStyles}>
          {panelState === "LOADING" &&
            Array.from({ length: SKELETON_ITEM_COUNT }, (_, index) => (
              <div key={index} className={Styles.panelSkeletonItemStyles}>
                <Skeleton width="45%" />
                <Skeleton width="80%" />
              </div>
            ))}

          {panelState === "ERROR" && (
            <div className={Styles.panelStateStyles} role="alert">
              <AlertCircle size={26} className="mb-2.5 text-destructive" />
              <div className={Styles.panelStateTitleStyles}>Couldn't load notifications</div>
              <div className={Styles.panelStateBodyStyles}>
                Your reminders still fire. This only affects the list.
              </div>
              <Button size="sm" className="mt-4" onClick={onRetry}>
                Try again
              </Button>
            </div>
          )}

          {panelState === "EMPTY" && (
            <div className={Styles.panelStateStyles}>
              <Bell size={26} className="mb-2.5 text-foreground-tertiary" />
              <div className={Styles.panelStateTitleStyles}>Nothing here yet</div>
              <div className={Styles.panelStateBodyStyles}>
                When a reminder fires, it lands here. Try{" "}
                <span className={Styles.inlineCommandStyles}>/remind</span> in Capture.
              </div>
            </div>
          )}

          {panelState === "LIST" && (
            <>
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  actionState={actionStates.get(notification.id) ?? null}
                  isOffline={isOffline}
                  defaultReminderTime={defaultReminderTime}
                  onOpen={onOpen}
                  onDone={onDone}
                  onSnooze={onSnooze}
                />
              ))}
              {hasMore && (
                <div className={Styles.panelLoadMoreStyles}>
                  <Button size="sm" disabled={isLoadingMore} onClick={onLoadMore}>
                    {isLoadingMore ? "Loading…" : "Load more"}
                  </Button>
                </div>
              )}
            </>
          )}
        </div>

        <div className={Styles.panelFootStyles}>
          Every reminder lands here, whatever your notification settings say. Cleared after 90
          days.
        </div>
      </aside>
    </>
  );
};

export default NotificationPanel;
