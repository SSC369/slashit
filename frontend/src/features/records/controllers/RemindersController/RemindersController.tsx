import { AlertCircle, LogIn, SearchX, WifiOff } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, type ReactElement } from "react";
import { useNavigate } from "react-router";

import useGetReminders from "../../../../api/queries/GetReminders/useGetReminders";
import { useResponseHandler } from "../../../../api/queries/GetReminders/responseHandler";
import { API_FAILED } from "../../../../constants/apiConstants";
import { MAX_ACTIVE_REMINDERS } from "../../../../constants/reminderConstants";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import { useStore } from "../../../../stores/StoreProvider";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import EmptyReminders from "../../components/EmptyReminders";
import ReminderListNotice from "../../components/ReminderListNotice";
import ReminderTable from "../../components/ReminderTable";
import * as RecordsStyles from "../../components/styles";
import * as Styles from "./styles";

const SEARCH_DEBOUNCE_MS = 250;

const SYNC_TIME_FORMAT = new Intl.DateTimeFormat(undefined, {
  hour: "numeric",
  minute: "2-digit",
});

type ListStateType = "SESSION_ENDED" | "ERROR" | "LOADING" | "EMPTY" | "NO_MATCH" | "LIST";

/**
 * The Reminders tab (FR-26): loads the three groups into the reminders store
 * and draws whichever state the load is in. Rendered by RecordsController,
 * which owns the tabs and the shared search box.
 */
const RemindersController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const isOnline = useOnlineStatus();
  const { triggerAPI, data, apiStatus, apiError } = useGetReminders();
  const { handleResponse } = useResponseHandler();

  const { searchText } = store.records;
  const trimmedSearch = searchText.trim();

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      triggerAPI({ search: trimmedSearch || null });
      // triggerAPI is left out on purpose, per repo-rules.md §13.4.
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timeoutId);
  }, [trimmedSearch]);

  useEffect(() => {
    if (!data) return;
    handleResponse({ data, onRemindersLoaded: (groups) => store.reminders.setGroups(groups) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const { lastSyncedAt, totalCount, activeCount } = store.reminders;
  const hasSyncedOnce = lastSyncedAt !== null;
  const hasFailed = apiStatus === API_FAILED;
  const isSessionEnded = hasFailed && isSessionEndedError(apiError);
  // Offline with a list already loaded: keep showing it (RemindersOffline).
  const isShowingSavedCopy = !isOnline && hasSyncedOnce;

  let listState: ListStateType = "LIST";
  if (isSessionEnded) listState = "SESSION_ENDED";
  else if (hasFailed && !isShowingSavedCopy) listState = "ERROR";
  else if (!hasSyncedOnce) listState = "LOADING";
  else if (totalCount === 0) listState = trimmedSearch ? "NO_MATCH" : "EMPTY";

  const handleRetry = (): void => {
    triggerAPI({ search: trimmedSearch || null });
  };

  const handleOpenReminder = (id: string): void => {
    navigate(`/records/reminders/${id}`);
  };

  const footLeft =
    isShowingSavedCopy && lastSyncedAt !== null
      ? `Showing what was saved on this device at ${SYNC_TIME_FORMAT.format(lastSyncedAt)}`
      : `${totalCount} ${totalCount === 1 ? "reminder" : "reminders"} · ${activeCount} active of ${MAX_ACTIVE_REMINDERS}`;

  switch (listState) {
    case "SESSION_ENDED":
      return (
        <ReminderListNotice
          icon={<LogIn size={24} />}
          title="Your session ended"
          body="Sign in again to see your reminders. Nothing was lost, and your reminders keep firing."
          actionLabel="Sign in"
          onAction={() => navigate("/sign-in")}
        />
      );
    case "ERROR":
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title="Couldn't load your reminders"
          body="They are safe, and they still fire on time. This is a connection problem on our side."
          actionLabel="Try again"
          onAction={handleRetry}
        />
      );
    case "EMPTY":
      return <EmptyReminders onStartCapturing={() => navigate("/")} />;
    case "NO_MATCH":
      return (
        <ReminderListNotice
          icon={<SearchX size={24} />}
          title={`No reminders match “${trimmedSearch}”`}
          body="Search covers reminder text. Try another word, or clear the search."
          actionLabel="Clear search"
          onAction={() => store.records.setSearchText("")}
        />
      );
    case "LOADING":
    case "LIST":
      return (
        <>
          {!isOnline && (
            <div className={RecordsStyles.offlineNoteStyles} role="status">
              <WifiOff size={16} className={Styles.offlineIconStyles} />
              <span>
                <span className={RecordsStyles.offlineNoteTitleStyles}>You are offline.</span>{" "}
                Reminders still fire and email still arrives. Pop-ups, Done, Snooze and edits need
                a connection.
              </span>
            </div>
          )}
          <ReminderTable
            needsAttention={store.reminders.getGroup("NEEDS_ATTENTION")}
            upcoming={store.reminders.getGroup("UPCOMING")}
            done={store.reminders.getGroup("DONE")}
            isLoading={listState === "LOADING"}
            footLeft={footLeft}
            onOpenReminder={handleOpenReminder}
          />
        </>
      );
    default: {
      const unhandled: never = listState;
      throw new Error(`Unhandled reminders list state: ${String(unhandled)}`);
    }
  }
};

export default observer(RemindersController);
