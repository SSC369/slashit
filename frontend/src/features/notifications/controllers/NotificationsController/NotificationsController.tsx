import { observer } from "mobx-react-lite";
import { useEffect, useRef, useState, type ReactElement } from "react";
import { useNavigate } from "react-router";

import { onLiveReconnected } from "../../../../api/lib/liveConnection";
import useMarkAllNotificationsRead from "../../../../api/mutations/MarkAllNotificationsRead/useMarkAllNotificationsRead";
import useMarkNotificationRead from "../../../../api/mutations/MarkNotificationRead/useMarkNotificationRead";
import useMarkReminderDone from "../../../../api/mutations/MarkReminderDone/useMarkReminderDone";
import useSnoozeReminder from "../../../../api/mutations/SnoozeReminder/useSnoozeReminder";
import { useResponseHandler as useNotificationsHandler } from "../../../../api/queries/GetNotifications/responseHandler";
import useGetNotifications from "../../../../api/queries/GetNotifications/useGetNotifications";
import { useResponseHandler as useSettingsHandler } from "../../../../api/queries/GetSettings/responseHandler";
import useGetSettings from "../../../../api/queries/GetSettings/useGetSettings";
import { useResponseHandler as useCountHandler } from "../../../../api/queries/GetUnreadNotificationCount/responseHandler";
import useGetUnreadNotificationCount from "../../../../api/queries/GetUnreadNotificationCount/useGetUnreadNotificationCount";
import useNotificationReceived from "../../../../api/subscriptions/NotificationReceived/useNotificationReceived";
import { API_FAILED, API_FETCHING } from "../../../../constants/apiConstants";
import type { NotificationFieldsFragment } from "../../../../fragments/NotificationFields.generated";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import { useStore } from "../../../../stores/StoreProvider";
import { formatInstantClock, type SnoozeOptionType } from "../../../../utils/formatNotification";
import NotificationPanel, { type PanelStateType } from "../../components/NotificationPanel";
import ReminderPopup from "../../components/ReminderPopup";
import * as NotificationStyles from "../../components/styles";
import * as Styles from "./styles";

const APP_TITLE = "Slashit";

/**
 * Everything notifications does across the app, mounted once in the shell:
 * the live feed (FR-13), the bell's count and tab title (FR-36), the panel
 * (FR-35, FR-37) and the pop-up stack with Done, Snooze and Open (FR-19 to
 * FR-22).
 */
const NotificationsController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const isOnline = useOnlineStatus();
  const [announcement, setAnnouncement] = useState("");
  const isLoadingMoreRef = useRef(false);
  const notifications = store.notifications;

  const { triggerAPI: triggerGetCount, data: countData } = useGetUnreadNotificationCount();
  const { handleResponse: handleCount } = useCountHandler();
  const { triggerAPI: triggerGetNotifications, data: listData, apiStatus: listStatus } =
    useGetNotifications();
  const { handleResponse: handleList } = useNotificationsHandler();
  const { triggerAPI: triggerGetSettings, data: settingsData } = useGetSettings();
  const { handleResponse: handleSettings } = useSettingsHandler();
  const { triggerAPI: triggerMarkRead } = useMarkNotificationRead();
  const { triggerAPI: triggerMarkAllRead } = useMarkAllNotificationsRead();
  const { triggerAPI: triggerMarkDone } = useMarkReminderDone();
  const { triggerAPI: triggerSnooze } = useSnoozeReminder();

  useNotificationReceived({
    isEnabled: true,
    onNotificationReceived: (notification) => {
      notifications.receive(notification);
      if (notification.showPopup) {
        const time = formatInstantClock(new Date(notification.occurredAt));
        setAnnouncement(`Reminder: ${notification.title}, ${time}`);
      }
    },
  });

  useEffect(() => {
    triggerGetCount();
    triggerGetSettings({ detectedTimezone: null });
    // Anything pushed while the socket was down was missed; read it back.
    return onLiveReconnected(() => {
      triggerGetCount();
      if (store.notifications.hasLoaded) triggerGetNotifications({ cursor: null });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!notifications.isPanelOpen || notifications.hasLoaded) return;
    triggerGetNotifications({ cursor: null });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notifications.isPanelOpen]);

  useEffect(() => {
    handleCount({ data: countData, onCountLoaded: notifications.setUnreadCount });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [countData]);

  useEffect(() => {
    handleList({
      data: listData,
      onNotificationsLoaded: (items, nextCursor) => {
        if (isLoadingMoreRef.current) notifications.appendPage(items, nextCursor);
        else notifications.setPage(items, nextCursor);
        isLoadingMoreRef.current = false;
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listData]);

  useEffect(() => {
    handleSettings({ data: settingsData, onSettingsLoaded: store.settings.setSettings });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settingsData]);

  const unreadCount = notifications.unreadCount;
  useEffect(() => {
    document.title = unreadCount > 0 ? `(${unreadCount}) ${APP_TITLE}` : APP_TITLE;
  }, [unreadCount]);

  const reportFailure = (notification: NotificationFieldsFragment, kind: "DONE" | "SNOOZE"): void => {
    notifications.setActionState(notification.id, { kind, status: "FAILED" });
  };

  const handleDone = (notification: NotificationFieldsFragment): void => {
    const reminderId = notification.targetId;
    if (reminderId === null) return;
    notifications.setActionState(notification.id, { kind: "DONE", status: "ACTING" });
    triggerMarkDone({
      id: reminderId,
      onReminderActed: (reminder) => {
        store.reminders.upsert(reminder);
        notifications.applyReminderAction(reminderId, "DONE");
      },
      // Deleted meanwhile: nothing left to act on, so the card goes.
      onReminderNotFound: () => notifications.applyReminderAction(reminderId, "DONE"),
      onRequestFailed: () => reportFailure(notification, "DONE"),
    });
  };

  const handleSnooze = (notification: NotificationFieldsFragment, option: SnoozeOptionType): void => {
    const reminderId = notification.targetId;
    if (reminderId === null) return;
    notifications.setActionState(notification.id, { kind: "SNOOZE", status: "ACTING" });
    triggerSnooze({
      id: reminderId,
      option,
      onReminderActed: (reminder) => {
        store.reminders.upsert(reminder);
        notifications.applyReminderAction(reminderId, "SNOOZED");
      },
      onReminderNotFound: () => notifications.applyReminderAction(reminderId, "SNOOZED"),
      onRequestFailed: () => reportFailure(notification, "SNOOZE"),
    });
  };

  const handleOpen = (notification: NotificationFieldsFragment): void => {
    notifications.closePopup(notification.id);
    notifications.setPanelOpen(false);
    if (!notification.read) {
      triggerMarkRead({ id: notification.id, onNotificationRead: notifications.upsert });
    }
    if (notification.targetId !== null) navigate(`/records/reminders/${notification.targetId}`);
  };

  const handleMarkAllRead = (): void => {
    triggerMarkAllRead({ onAllRead: () => notifications.markAllReadLocally() });
  };

  const handleLoadMore = (): void => {
    if (notifications.nextCursor === null) return;
    isLoadingMoreRef.current = true;
    triggerGetNotifications({ cursor: notifications.nextCursor });
  };

  const hasListFailed = listStatus === API_FAILED;
  let panelState: PanelStateType = "LIST";
  if (!notifications.hasLoaded) panelState = hasListFailed ? "ERROR" : "LOADING";
  else if (notifications.order.length === 0) panelState = "EMPTY";

  const popupProps = {
    isOffline: !isOnline,
    defaultReminderTime: store.settings.defaultReminderTime,
    onDone: handleDone,
    onSnooze: handleSnooze,
    onOpen: handleOpen,
    onClose: (notification: NotificationFieldsFragment) => notifications.closePopup(notification.id),
  };

  return (
    <>
      {notifications.isPanelOpen && (
        <NotificationPanel
          panelState={panelState}
          notifications={notifications.getAll()}
          unreadCount={unreadCount}
          hasMore={notifications.nextCursor !== null}
          isLoadingMore={listStatus === API_FETCHING && isLoadingMoreRef.current}
          isOffline={!isOnline}
          defaultReminderTime={store.settings.defaultReminderTime}
          actionStates={notifications.actionStates}
          onClose={() => notifications.setPanelOpen(false)}
          onRetry={() => triggerGetNotifications({ cursor: null })}
          onLoadMore={handleLoadMore}
          onMarkAllRead={handleMarkAllRead}
          onOpen={handleOpen}
          onDone={handleDone}
          onSnooze={handleSnooze}
        />
      )}
      <div className={NotificationStyles.popupStackStyles}>
        {notifications.getPopups().map((notification) => (
          <ReminderPopup
            key={notification.id}
            notification={notification}
            actionState={notifications.actionStates.get(notification.id) ?? null}
            {...popupProps}
          />
        ))}
      </div>
      <div className={Styles.liveRegionStyles} aria-live="polite" role="status">
        {announcement}
      </div>
    </>
  );
};

export default observer(NotificationsController);
