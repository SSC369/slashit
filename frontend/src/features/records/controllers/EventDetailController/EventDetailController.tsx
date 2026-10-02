import { AlertCircle, ChevronRight, FileQuestion, LogIn } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useState, type ReactElement } from "react";
import { useNavigate, useParams } from "react-router";

import useGetEvent from "../../../../api/queries/GetEvent/useGetEvent";
import { useResponseHandler } from "../../../../api/queries/GetEvent/responseHandler";
import { API_FAILED } from "../../../../constants/apiConstants";
import PageTopbar from "../../../../components/PageTopbar";
import { useStore } from "../../../../stores/StoreProvider";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import EventDetailView, { EventDetailSkeleton } from "../../components/EventDetailView";
import ReminderListNotice from "../../components/ReminderListNotice";
import * as RecordsStyles from "../../components/styles";
import * as Styles from "./styles";

/**
 * One event at `/records/events/:id` (FR-27), read from the events store so
 * a capture made in this session shows at once. Every state of
 * `EventDetailStates` is drawn here. Edit and delete arrive in slice 2.
 */
const EventDetailController = (): ReactElement => {
  const { id = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const store = useStore();
  const [isNotFound, setIsNotFound] = useState(false);

  const { triggerAPI, data, apiStatus, apiError } = useGetEvent();
  const { handleResponse } = useResponseHandler();

  useEffect(() => {
    if (!id) return;
    setIsNotFound(false);
    triggerAPI({ id });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!data) return;
    handleResponse({
      data,
      onEventLoaded: (event) => store.events.upsert(event),
      onEventNotFound: () => {
        store.events.remove(id);
        setIsNotFound(true);
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const event = store.events.get(id);
  const hasLoadFailed = apiStatus === API_FAILED;
  const isSessionEnded = hasLoadFailed && isSessionEndedError(apiError);

  const goToEvents = (): void => {
    store.records.setKindFilter("EVENTS");
    navigate("/records");
  };

  const renderBody = (): ReactElement => {
    if (isNotFound) {
      return (
        <ReminderListNotice
          icon={<FileQuestion size={24} />}
          title="This event doesn't exist or was deleted"
          body="It may have been deleted in another tab. Its alert was removed with it."
          actionLabel="Back to events"
          onAction={goToEvents}
        />
      );
    }
    if (isSessionEnded) {
      return (
        <ReminderListNotice
          icon={<LogIn size={24} />}
          title="Your session ended"
          body="Sign in again to see this event."
          actionLabel="Sign in"
          onAction={() => navigate("/sign-in")}
        />
      );
    }
    // A copy already held stays readable when a refresh fails, as offline.
    if (hasLoadFailed && event === null) {
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title="Couldn't load this event"
          body="It is safe. Try again in a moment."
          actionLabel="Try again"
          onAction={() => triggerAPI({ id })}
        />
      );
    }
    if (event === null) return <EventDetailSkeleton />;
    return <EventDetailView event={event} />;
  };

  return (
    <div className={Styles.pageStyles}>
      <PageTopbar title="Event" />
      <div className={RecordsStyles.paneStyles}>
        <div className={Styles.contentStyles}>
          <div className={RecordsStyles.breadcrumbStyles}>
            <span className={Styles.breadcrumbLinkStyles} onClick={() => navigate("/records")}>
              Records
            </span>
            <ChevronRight size={13} />
            <span className={Styles.breadcrumbLinkStyles} onClick={goToEvents}>
              Events
            </span>
          </div>
          {renderBody()}
        </div>
      </div>
    </div>
  );
};

export default observer(EventDetailController);
