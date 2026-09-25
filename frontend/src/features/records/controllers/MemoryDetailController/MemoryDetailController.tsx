import { AlertCircle, ChevronRight, FileQuestion, LogIn } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useState, type ReactElement } from "react";
import { useNavigate, useParams } from "react-router";

import useUpdateMemory from "../../../../api/mutations/UpdateMemory/useUpdateMemory";
import useGetMemory from "../../../../api/queries/GetMemory/useGetMemory";
import { useResponseHandler } from "../../../../api/queries/GetMemory/responseHandler";
import PageTopbar from "../../../../components/PageTopbar";
import { API_FAILED, API_FETCHING } from "../../../../constants/apiConstants";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import { useStore } from "../../../../stores/StoreProvider";
import { isSessionEndedError } from "../../../../utils/isSessionEndedError";
import MemoryDetailView, { MemoryDetailSkeleton } from "../../components/MemoryDetailView";
import MemoryEditForm, {
  type MemoryDraft,
  type MemoryEditBannerType,
} from "../../components/MemoryEditForm";
import ReminderListNotice from "../../components/ReminderListNotice";
import * as RecordsStyles from "../../components/styles";
import * as Styles from "./styles";

export type MemoryDetailModeType = "VIEW" | "EDIT";

interface MemoryDetailControllerProps {
  mode: MemoryDetailModeType;
}

/**
 * One memory at `/records/memories/:id` (FR-17) and its edit form at
 * `.../edit` (FR-18). Forget is slice 3's (sub-plan 4.3).
 */
const MemoryDetailController = (props: MemoryDetailControllerProps): ReactElement => {
  const { mode } = props;
  const { id = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const store = useStore();
  const isOnline = useOnlineStatus();

  const [isNotFound, setIsNotFound] = useState(false);
  const [draft, setDraft] = useState<MemoryDraft | null>(null);
  const [textError, setTextError] = useState<string | null>(null);
  const [banner, setBanner] = useState<MemoryEditBannerType>("NONE");

  const { triggerAPI: triggerGetMemory, data, apiStatus, apiError } = useGetMemory();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: triggerUpdateMemory, apiStatus: updateApiStatus } = useUpdateMemory();

  const memory = store.memories.get(id);
  const isEditing = mode === "EDIT";
  const hasMemory = memory !== null;

  useEffect(() => {
    if (!id) return;
    setIsNotFound(false);
    triggerGetMemory({ id });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!data) return;
    handleResponse({
      data,
      onMemoryLoaded: (loaded) => store.memories.upsert(loaded),
      onMemoryNotFound: () => setIsNotFound(true),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  // A fresh draft each time the form opens; never while it is being typed in.
  useEffect(() => {
    if (!isEditing || memory === null) {
      setDraft(null);
      return;
    }
    setDraft({ text: memory.text, category: memory.category });
    setTextError(null);
    setBanner("NONE");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditing, hasMemory, id]);

  const goToMemories = (): void => {
    store.records.setKindFilter("MEMORIES");
    navigate("/records");
  };

  const handleDraftChange = (patch: Partial<MemoryDraft>): void => {
    setDraft((current) => (current === null ? current : { ...current, ...patch }));
    if ("text" in patch) setTextError(null);
  };

  const handleSave = (): void => {
    if (draft === null) return;
    setBanner("NONE");
    triggerUpdateMemory({
      id,
      text: draft.text.trim(),
      category: draft.category,
      onMemoryUpdated: (updated) => {
        store.memories.upsert(updated);
        store.toast.show({ message: "Memory updated.", linkLabel: "View", linkTo: `/records/memories/${updated.id}` });
        navigate(`/records/memories/${updated.id}`);
      },
      onMemoryTooLong: ({ message }) => setTextError(message),
      onInvalidMemory: (message) => setTextError(message),
      onMemoryNotFound: () => setBanner("GONE"),
      onRequestFailed: () => setBanner("FAILED"),
    });
  };

  const isSessionEnded = apiStatus === API_FAILED && isSessionEndedError(apiError);
  const hasLoadFailed = apiStatus === API_FAILED && memory === null;

  const renderBody = (): ReactElement => {
    if (isNotFound) {
      return (
        <ReminderListNotice
          icon={<FileQuestion size={24} />}
          title="This memory doesn't exist or was forgotten"
          body="It may have been forgotten from another tab or device."
          actionLabel="Back to memories"
          onAction={goToMemories}
        />
      );
    }
    if (isSessionEnded) {
      return (
        <ReminderListNotice
          icon={<LogIn size={24} />}
          title="Sign in to see your memories"
          body="Your session ended. Memories are only ever shown to the account that saved them."
          actionLabel="Sign in"
          onAction={() => navigate("/sign-in")}
        />
      );
    }
    if (hasLoadFailed) {
      return (
        <ReminderListNotice
          icon={<AlertCircle size={24} />}
          title="Couldn't load this memory"
          body="Nothing is lost. Check your connection and try again."
          actionLabel="Try again"
          onAction={() => triggerGetMemory({ id })}
        />
      );
    }
    if (memory === null) return <MemoryDetailSkeleton />;
    if (isEditing && draft !== null) {
      return (
        <MemoryEditForm
          draft={draft}
          textError={textError}
          banner={banner}
          isSaving={updateApiStatus === API_FETCHING}
          isOffline={!isOnline}
          onChange={handleDraftChange}
          onSave={handleSave}
          onCancel={() => (banner === "GONE" ? goToMemories() : navigate(`/records/memories/${id}`))}
        />
      );
    }
    return (
      <MemoryDetailView
        memory={memory}
        isOffline={!isOnline}
        onEdit={() => navigate(`/records/memories/${id}/edit`)}
      />
    );
  };

  return (
    <div className={Styles.pageStyles}>
      <PageTopbar title="Records" />
      <div className={Styles.paneStyles}>
        <div className={Styles.contentStyles}>
          <div className={RecordsStyles.breadcrumbStyles}>
            <span className={Styles.breadcrumbLinkStyles} onClick={() => navigate("/records")}>
              Records
            </span>
            <ChevronRight size={13} />
            <span className={Styles.breadcrumbLinkStyles} onClick={goToMemories}>
              Memories
            </span>
            {memory !== null && (
              <>
                <ChevronRight size={13} />
                <span className={RecordsStyles.breadcrumbCurrentStyles}>{memory.text}</span>
                {isEditing && <span>· Editing</span>}
              </>
            )}
          </div>
          {renderBody()}
        </div>
      </div>
    </div>
  );
};

export default observer(MemoryDetailController);
