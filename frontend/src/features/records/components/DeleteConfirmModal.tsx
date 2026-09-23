import { TrashIcon } from "lucide-react";
import type { ReactElement, ReactNode } from "react";

import BusyButton from "../../../components/BusyButton";
import Button from "../../../design-system/components/Button";
import * as Styles from "./styles";

interface DeleteConfirmModalProps {
  title: string;
  message: ReactNode;
  confirmLabel: string;
  /** While the delete runs: a spinner replaces the confirm label and Cancel
   * locks (`DeleteReminderBusy`). */
  isBusy?: boolean;
  /** Shown inside the dialog when the delete failed; the confirm button then
   * reads "Try again" (`DeleteReminderFailed`). */
  errorMessage?: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

const DeleteConfirmModal = (props: DeleteConfirmModalProps): ReactElement => {
  const {
    title,
    message,
    confirmLabel,
    isBusy = false,
    errorMessage = null,
    onCancel,
    onConfirm,
  } = props;

  return (
    <div className={Styles.modalOverlayStyles}>
      <div className={Styles.modalStyles} role="dialog" aria-modal="true" aria-label={title}>
        <div className={Styles.modalBodyStyles}>
          <TrashIcon size={22} className="shrink-0 text-destructive" />
          <div>
            <div className={Styles.modalTitleStyles}>{title}</div>
            <div className={Styles.modalMessageStyles}>{message}</div>
            {errorMessage !== null && (
              <div className={Styles.modalErrorStyles} role="alert">
                {errorMessage}
              </div>
            )}
          </div>
        </div>
        <div className={Styles.modalActionsStyles}>
          <Button onClick={onCancel} disabled={isBusy}>
            Cancel
          </Button>
          <BusyButton variant="danger" isBusy={isBusy} busyLabel="Deleting" onClick={onConfirm}>
            {errorMessage !== null ? "Try again" : confirmLabel}
          </BusyButton>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmModal;
