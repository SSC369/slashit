import { AlertCircle, ChevronRight, FileQuestion, LogIn } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useState, type ReactElement } from "react";
import { useNavigate, useParams } from "react-router";

import useDeleteReminder from "../../../../api/mutations/DeleteReminder/useDeleteReminder";
import useMarkReminderDone from "../../../../api/mutations/MarkReminderDone/useMarkReminderDone";
import useSnoozeReminder from "../../../../api/mutations/SnoozeReminder/useSnoozeReminder";
import useUpdateReminder from "../../../../api/mutations/UpdateReminder/useUpdateReminder";
import useGetReminder from "../../../../api/queries/GetReminder/useGetReminder";
import { useResponseHandler } from "../../../../api/queries/GetReminder/responseHandler";
import { API_FAILED, API_FETCHING } from "../../../../constants/apiConstants";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import type { ReminderFieldsFragment } from "../../../../fragments/ReminderFields.generated";
import type { NotificationActionState } from "../../../../stores/NotificationsStore";
import { useStore } from "../../../../stores/StoreProvider";
import type { SnoozeOptionType } from "../../../../utils/formatNotification";
import { formatReminderDateTime } from "../../../../utils/formatReminder";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import PageTopbar from "../../../../components/PageTopbar";
import {
  draftFromReminder,
  validateDraft,
  type ReminderDraft,
  type ReminderFieldErrors,
} from "../../../../utils/reminderDraft";
import DeleteConfirmModal from "../../components/DeleteConfirmModal";
import ReminderDetailView, { ReminderDetailSkeleton } from "../../components/ReminderDetailView";
import ReminderEditForm, { type EditBannerType } from "../../components/ReminderEditForm";
import ReminderListNotice from "../../components/ReminderListNotice";
import * as RecordsStyles from "../../components/styles";
import * as Styles from "./styles";

export type ReminderDetailModeType = "VIEW" | "EDIT";

interface ReminderDetailControllerProps {
  mode: ReminderDetailModeType;
}

/**
 * One reminder at `/records/reminders/:id` (FR-27) and its edit form at
 * `.../edit` (FR-28), with delete (FR-29). Every state of canvas page 8's
 * detail artboards is drawn here or in the components it renders.
 */
const ReminderDetailController = (props: ReminderDetailControllerProps): ReactElement => {
  const { mode } = props;
  const { id = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const store = useStore();
  const isOnline = useOnlineStatus();

  const [isNotFound, setIsNotFound] = useState(false);
  const [draft, setDraft] = useState<ReminderDraft | null>(null);
  const [serverErrors, setServerErrors] = useState<ReminderFieldErrors>({});
  const [editBanner, setEditBanner] = useState<EditBannerType>("NONE");
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [actionState, setActionState] = useState<NotificationActionState | null>(null);

  const { triggerAPI: triggerGetReminder, data, apiStatus, apiError } = useGetReminder();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: triggerUpdateReminder, apiStatus: updateApiStatus } = useUpdateReminder();
  const { triggerAPI: triggerDeleteReminder, apiStatus: deleteApiStatus } = useDeleteReminder();
  const { triggerAPI: triggerMarkDone } = useMarkReminderDone();
  const { triggerAPI: triggerSnooze } = useSnoozeReminder();

  const reminder = store.reminders.get(id);
  const isEditing = mode === "EDIT";
  const hasReminder = reminder !== null;

  useEffect(() => {
    if (!id) return;
    setIsNotFound(false);
    triggerGetReminder({ id });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!data) return;
    handleResponse({
      data,
      onReminderLoaded: (loaded) => store.reminders.upsert(loaded),
      onReminderNotFound: () => setIsNotFound(true),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  // A fresh draft each time the form opens; never while it is being typed in.
  useEffect(() => {
    if (!isEditing || reminder === null) {
      setDraft(null);
      return;
    }
    setDraft(draftFromReminder(reminder));
    setServerErrors({});
    setEditBanner("NONE");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditing, hasReminder, id]);

  const goToReminders = (): void => {
    store.records.setKindFilter("REMINDERS");
    navigate("/records");
  };

  const handleDraftChange = (patch: Partial<ReminderDraft>): void => {
    setDraft((current) => (current === null ? current : { ...current, ...patch }));
    // A server error names the value it refused; a new value clears it.
    setServerErrors((current) => {
      const next = { ...current };
      for (const field of Object.keys(patch) as (keyof ReminderDraft)[]) delete next[field];
      if ("startDate" in patch) delete next.localTime;
      return next;
    });
  };

  const handleSave = (): void => {
    if (draft === null) return;
    triggerUpdateReminder({
      id,
      description: draft.description.trim(),
      startDate: draft.startDate,
      localTime: draft.localTime,
      repeatKind: draft.repeatKind,
      repeatInterval: draft.repeatInterval,
      repeatWeekdays: draft.repeatKind === "WEEKLY" ? draft.repeatWeekdays : [],
      onReminderUpdated: (updated) => {
        store.reminders.upsert(updated);
        store.toast.show({
          message:
            updated.nextFireAt !== null
              ? `Reminder updated. Next: ${formatReminderDateTime(updated.nextFireAt, updated.scheduleTimezone)}`
              : "Reminder updated.",
          linkLabel: "View",
          linkTo: `/records/reminders/${updated.id}`,
        });
        navigate(`/records/reminders/${updated.id}`);
      },
      onInvalidReminder: ({ field, message }) =>
        setServerErrors((current) => ({ ...current, [field]: message })),
      onReminderTimePassed: (message) =>
        setServerErrors((current) => ({ ...current, localTime: message })),
      onReminderDeleted: () => setEditBanner("GONE"),
      onReminderNotFound: () => setIsNotFound(true),
      onRequestFailed: () => setEditBanner("FAILED"),
    });
  };

  const handleConfirmDelete = (): void => {
    setDeleteError(null);
    const removeAndLeave = (): void => {
      store.reminders.remove(id);
      store.records.remove(id);
      setIsDeleteOpen(false);
      goToReminders();
    };
    triggerDeleteReminder({
      id,
      onReminderDeleted: removeAndLeave,
      // Already gone elsewhere: the outcome the user asked for.
      onReminderNotFound: removeAndLeave,
      onRequestFailed: () => setDeleteError("Couldn't delete it. The reminder is unchanged. Try again."),
    });
  };

  const applyAction = (updated: ReminderFieldsFragment, action: "DONE" | "SNOOZED"): void => {
    store.reminders.upsert(updated);
    store.notifications.applyReminderAction(updated.id, action);
    setActionState(null);
  };

  const handleDone = (target: ReminderFieldsFragment): void => {
    setActionState({ kind: "DONE", status: "ACTING" });
    triggerMarkDone({
      id: target.id,
      onReminderActed: (updated) => applyAction(updated, "DONE"),
      onReminderNotFound: () => setIsNotFound(true),
      onRequestFailed: () => setActionState({ kind: "DONE", status: "FAILED" }),
    });
  };

  const handleSnooze = (target: ReminderFieldsFragment, option: SnoozeOptionType): void => {
    setActionState({ kind: "SNOOZE", status: "ACTING" });
    triggerSnooze({
      id: target.id,
      option,
      onReminderActed: (updated) => applyAction(updated, "SNOOZED"),
      onReminderNotFound: () => setIsNotFound(true),
      onRequestFailed: () => setActionState({ kind: "SNOOZE", status: "FAILED" }),
    });
  };

  const isSessionEnded = apiStatus === API_FAILED && isSessionEndedError(apiError);
  const hasLoadFailed = apiStatus === API_FAILED && reminder === null;

  const renderBody = (): ReactElement => {
    if (isNotFound) {
      return (
        <ReminderListNotice
          icon={<FileQuestion size={24} />}
          title="This reminder doesn't exist or was deleted"
          body="It may have been deleted from another tab or device. Deleted reminders never fire."
          actionLabel="Back to reminders"
          onAction={goToReminders}
        />
      );
    }
    if (isSessionEnded) {
      return (
        <ReminderListNotice
          icon={<LogIn size={24} />}
          title="Your session ended"
          body="Sign in again to see your reminders. Nothing was lost, and your reminders keep firing."
          actionLabel="Sign in"
          onAction={() => navigate("/sign-in")}
        />
      );
    }
    if (hasLoadFailed) {
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title="Couldn't load this reminder"
          body="It is safe, and it still fires on time. This is a connection problem on our side."
          actionLabel="Try again"
          onAction={() => triggerGetReminder({ id })}
        />
      );
    }
    if (reminder === null) return <ReminderDetailSkeleton />;
    if (isEditing && draft !== null) {
      const fieldErrors = { ...validateDraft(draft), ...serverErrors };
      return (
        <>
          <div className={RecordsStyles.detailTitleStyles}>Edit reminder</div>
          <div className={RecordsStyles.detailFieldsStyles}>
            <ReminderEditForm
              draft={draft}
              timezone={reminder.scheduleTimezone}
              fieldErrors={fieldErrors}
              banner={editBanner}
              isSaving={updateApiStatus === API_FETCHING}
              isOffline={!isOnline}
              onChange={handleDraftChange}
              onSave={handleSave}
              onCancel={() =>
                editBanner === "GONE" ? goToReminders() : navigate(`/records/reminders/${id}`)
              }
            />
          </div>
        </>
      );
    }
    return (
      <ReminderDetailView
        reminder={reminder}
        isOffline={!isOnline}
        actionState={actionState}
        defaultReminderTime={store.settings.defaultReminderTime}
        onEdit={() => navigate(`/records/reminders/${id}/edit`)}
        onDelete={() => {
          setDeleteError(null);
          setIsDeleteOpen(true);
        }}
        onDone={handleDone}
        onSnooze={handleSnooze}
      />
    );
  };

  const isRepeating = reminder !== null && reminder.repeatKind !== "NONE";

  return (
    <div className={Styles.pageStyles}>
      <PageTopbar title="Reminder" />
      <div className={Styles.paneStyles}>
        <div className={Styles.contentStyles}>
          <div className={RecordsStyles.breadcrumbStyles}>
            <span className={Styles.breadcrumbLinkStyles} onClick={() => navigate("/records")}>
              Records
            </span>
            <ChevronRight size={13} />
            <span className={Styles.breadcrumbLinkStyles} onClick={goToReminders}>
              Reminders
            </span>
            {isEditing && reminder !== null && (
              <>
                <ChevronRight size={13} />
                <span className={RecordsStyles.breadcrumbCurrentStyles}>{reminder.description}</span>
              </>
            )}
          </div>
          {renderBody()}
        </div>
      </div>

      {isDeleteOpen && reminder !== null && (
        <DeleteConfirmModal
          title="Delete this reminder?"
          message={
            isRepeating
              ? `“${reminder.description}” repeats ${reminder.repeatText.charAt(0).toLowerCase()}${reminder.repeatText.slice(1)}. Deleting it removes the whole series, and it will not fire again.`
              : `Deleting “${reminder.description}” means it will not fire. This cannot be undone.`
          }
          confirmLabel="Delete reminder"
          isBusy={deleteApiStatus === API_FETCHING}
          errorMessage={deleteError}
          onCancel={() => setIsDeleteOpen(false)}
          onConfirm={handleConfirmDelete}
        />
      )}
    </div>
  );
};

export default observer(ReminderDetailController);
