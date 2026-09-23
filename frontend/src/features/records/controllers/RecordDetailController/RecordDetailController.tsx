import { ChevronRight } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useState, type ChangeEvent, type ReactElement } from "react";
import { useNavigate, useParams } from "react-router";

import useDeleteTask from "../../../../api/mutations/DeleteTask/useDeleteTask";
import useUpdateTask from "../../../../api/mutations/UpdateTask/useUpdateTask";
import useGetRecordDetail from "../../../../api/queries/GetRecordDetail/useGetRecordDetail";
import { useResponseHandler } from "../../../../api/queries/GetRecordDetail/responseHandler";
import { API_FETCHING } from "../../../../constants/apiConstants";
import Button from "../../../../design-system/components/Button";
import { useStore } from "../../../../stores/StoreProvider";
import PageTopbar from "../../../../components/PageTopbar";
import DeleteConfirmModal from "../../components/DeleteConfirmModal";
import RecordEditForm, { type EditableStatus } from "../../components/RecordEditForm";
import * as RecordsStyles from "../../components/styles";
import {
  formatLongDate,
  formatLongDateTime,
  fromDateTimeLocalInputValue,
} from "../../../../utils/formatDate";
import * as Styles from "./styles";

const RecordDetailController = (): ReactElement => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const store = useStore();

  const [isEditing, setIsEditing] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftStatus, setDraftStatus] = useState<EditableStatus>("PENDING");
  const [draftDueAt, setDraftDueAt] = useState<string | null>(null);

  const { triggerAPI: triggerGetRecordDetail, data } = useGetRecordDetail();
  const { handleResponse } = useResponseHandler();
  const { triggerAPI: triggerUpdateTask, apiStatus: updateTaskApiStatus } = useUpdateTask();
  const { triggerAPI: triggerDeleteTask } = useDeleteTask();

  useEffect(() => {
    if (!id) return;
    triggerGetRecordDetail({ id });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!data) return;
    handleResponse({
      data,
      onRecordLoaded: (task) => {
        store.records.upsert(task);
        setDraftTitle(task.title);
        setDraftStatus(task.status === "done" ? "DONE" : "PENDING");
        setDraftDueAt(task.dueAt);
        setNotFound(false);
      },
      onRecordNotFound: () => setNotFound(true),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const task = id ? store.records.records.get(id) : undefined;

  const handleTitleChange = (event: ChangeEvent<HTMLInputElement>): void => {
    setDraftTitle(event.target.value);
  };

  const handleDueAtChange = (event: ChangeEvent<HTMLInputElement>): void => {
    setDraftDueAt(fromDateTimeLocalInputValue(event.target.value));
  };

  const handleSave = (): void => {
    if (!id) return;
    triggerUpdateTask({
      id,
      title: draftTitle,
      status: draftStatus,
      dueAt: draftDueAt,
      onTaskUpdated: (updated) => {
        store.records.upsert(updated);
        setIsEditing(false);
      },
      onRecordNotFound: () => setNotFound(true),
    });
  };

  const handleCancelEdit = (): void => {
    if (task) {
      setDraftTitle(task.title);
      setDraftStatus(task.status === "done" ? "DONE" : "PENDING");
      setDraftDueAt(task.dueAt);
    }
    setIsEditing(false);
  };

  const handleConfirmDelete = (): void => {
    if (!id) return;
    triggerDeleteTask({
      ids: [id],
      onDeleted: () => {
        store.records.remove(id);
        navigate("/records");
      },
    });
  };

  if (notFound) {
    return (
      <div className={Styles.pageStyles}>
        <PageTopbar title="Records" />
        <div className={Styles.paneStyles}>
          <div className={Styles.contentStyles}>
            This record no longer exists.{" "}
            <span
              className="cursor-pointer text-accent"
              onClick={() => navigate("/records")}
            >
              Back to Records
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className={Styles.pageStyles}>
        <PageTopbar title="Records" />
        <div className={Styles.paneStyles}>
          <div className={Styles.contentStyles}>
            <div className={RecordsStyles.skeletonBlockStyles} style={{ width: "40%", height: 20 }} />
            <div className={RecordsStyles.detailFieldsStyles}>
              {Array.from({ length: 5 }, (_, index) => (
                <div key={index} className={RecordsStyles.detailRowStyles}>
                  <div className={RecordsStyles.detailLabelStyles}>&nbsp;</div>
                  <div className={RecordsStyles.skeletonBlockStyles} style={{ width: "50%" }} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={Styles.pageStyles}>
      <PageTopbar title="Records" />
      <div className={Styles.paneStyles}>
        <div className={Styles.contentStyles}>
          <div className={RecordsStyles.breadcrumbStyles}>
            <span className="cursor-pointer" onClick={() => navigate("/records")}>
              Records
            </span>
            <ChevronRight size={13} />
            <span>Tasks</span>
            <ChevronRight size={13} />
            <span className={RecordsStyles.breadcrumbCurrentStyles}>{task.title}</span>
          </div>

          {isEditing ? (
            <RecordEditForm
              title={draftTitle}
              dueAt={draftDueAt}
              status={draftStatus}
              isSaving={updateTaskApiStatus === API_FETCHING}
              onTitleChange={handleTitleChange}
              onDueAtChange={handleDueAtChange}
              onStatusChange={setDraftStatus}
              onSave={handleSave}
              onCancel={handleCancelEdit}
            />
          ) : (
            <>
              <div className={RecordsStyles.detailTitleStyles}>{task.title}</div>
              <div className={RecordsStyles.detailFieldsStyles}>
                <div className={RecordsStyles.detailRowStyles}>
                  <div className={RecordsStyles.detailLabelStyles}>Due</div>
                  <div className={RecordsStyles.detailValueStyles}>
                    {formatLongDate(task.dueAt)}
                  </div>
                </div>
                <div className={RecordsStyles.detailRowStyles}>
                  <div className={RecordsStyles.detailLabelStyles}>Status</div>
                  <div className={RecordsStyles.detailValueStyles}>
                    {task.status === "done" ? "Done" : "Pending"}
                  </div>
                </div>
                <div className={RecordsStyles.detailRowStyles}>
                  <div className={RecordsStyles.detailLabelStyles}>Created</div>
                  <div className={RecordsStyles.detailValueStyles}>
                    {formatLongDateTime(task.createdAt)}
                  </div>
                </div>
                <div className={RecordsStyles.detailRowStyles}>
                  <div className={RecordsStyles.detailLabelStyles}>Last edited</div>
                  <div className={RecordsStyles.detailValueStyles}>
                    {task.updatedAt === task.createdAt
                      ? "Never"
                      : formatLongDateTime(task.updatedAt)}
                  </div>
                </div>
                <div className={RecordsStyles.detailRowStyles}>
                  <div className={RecordsStyles.detailLabelStyles}>Origin</div>
                  <div className={RecordsStyles.detailValueStyles}>
                    {task.origin === "command" ? "Command" : "Edit"}
                  </div>
                </div>
              </div>
              {task.originalInput && (
                <div className={RecordsStyles.detailInputBlockStyles}>
                  <div className={RecordsStyles.formLabelStyles}>What you typed</div>
                  <div className={RecordsStyles.detailInputEchoStyles}>
                    {task.originalInput}
                  </div>
                </div>
              )}
              <div className={RecordsStyles.detailActionsRowStyles}>
                <Button onClick={() => setIsEditing(true)}>Edit</Button>
                <Button onClick={() => setIsDeleteConfirmOpen(true)}>Delete</Button>
              </div>
            </>
          )}
        </div>
      </div>

      {isDeleteConfirmOpen && (
        <DeleteConfirmModal
          title="Delete this task?"
          message={
            <>
              <span className={RecordsStyles.modalTaskNameStyles}>{task.title}</span> will be
              removed from your records. This cannot be undone.
            </>
          }
          confirmLabel="Delete task"
          onCancel={() => setIsDeleteConfirmOpen(false)}
          onConfirm={handleConfirmDelete}
        />
      )}
    </div>
  );
};

export default observer(RecordDetailController);
