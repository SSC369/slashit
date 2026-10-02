import { AlertCircle, CalendarDays, LogIn, WifiOff } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, type ReactElement } from "react";
import { useNavigate } from "react-router";

import useGetEvents from "../../../../api/queries/GetEvents/useGetEvents";
import { useResponseHandler } from "../../../../api/queries/GetEvents/responseHandler";
import { API_FAILED } from "../../../../constants/apiConstants";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import { useStore } from "../../../../stores/StoreProvider";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import EventTable from "../../components/EventTable";
import ReminderListNotice from "../../components/ReminderListNotice";
import * as RecordsStyles from "../../components/styles";
import * as Styles from "./styles";

type ListStateType = "SESSION_ENDED" | "ERROR" | "LOADING" | "EMPTY" | "LIST";

/**
 * The Events tab (FR-25, FR-26): loads every event into the events store and
 * draws whichever state the load is in (`RecordsEventsStates`). Rendered by
 * RecordsController, which owns the tabs.
 */
const EventsController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const isOnline = useOnlineStatus();
  const { triggerAPI, data, apiStatus, apiError } = useGetEvents();
  const { handleResponse } = useResponseHandler();

  useEffect(() => {
    triggerAPI({ scope: "ALL" });
    // triggerAPI is left out on purpose, per repo-rules.md §13.4.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!data) return;
    handleResponse({ data, onEventsLoaded: (events) => store.events.setAll(events) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const { lastSyncedAt, totalCount } = store.events;
  const hasSyncedOnce = lastSyncedAt !== null;
  const hasFailed = apiStatus === API_FAILED;
  const isSessionEnded = hasFailed && isSessionEndedError(apiError);
  // Offline with a list already loaded: keep showing it.
  const isShowingSavedCopy = !isOnline && hasSyncedOnce;

  let listState: ListStateType = "LIST";
  if (isSessionEnded) listState = "SESSION_ENDED";
  else if (hasFailed && !isShowingSavedCopy) listState = "ERROR";
  else if (!hasSyncedOnce) listState = "LOADING";
  else if (totalCount === 0) listState = "EMPTY";

  const handleOpenEvent = (id: string): void => {
    navigate(`/records/events/${id}`);
  };

  switch (listState) {
    case "SESSION_ENDED":
      return (
        <ReminderListNotice
          icon={<LogIn size={24} />}
          title="Your session ended"
          body="Sign in again to see your events. Nothing was lost."
          actionLabel="Sign in"
          onAction={() => navigate("/sign-in")}
        />
      );
    case "ERROR":
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title="Couldn't load your events"
          body="They are safe, and alerts still fire on time."
          actionLabel="Try again"
          onAction={() => triggerAPI({ scope: "ALL" })}
        />
      );
    case "EMPTY":
      return (
        <ReminderListNotice
          icon={<CalendarDays size={24} />}
          title="No events yet"
          body="Add one from Capture with /add-event."
          actionLabel="Go to Capture"
          onAction={() => navigate("/")}
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
                <span className={RecordsStyles.offlineNoteTitleStyles}>You are offline.</span> Events
                already loaded stay readable. Edits and deletes need a connection. Alerts still fire.
              </span>
            </div>
          )}
          <EventTable
            upcoming={store.events.upcoming}
            past={store.events.past}
            isLoading={listState === "LOADING"}
            onOpenEvent={handleOpenEvent}
          />
        </>
      );
    default: {
      const unhandled: never = listState;
      throw new Error(`Unhandled events list state: ${String(unhandled)}`);
    }
  }
};

export default observer(EventsController);
