import { Eraser } from "lucide-react";
import type { ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import Button from "../../../design-system/components/Button";
import { BACKUP_LINE } from "../../../constants/memoryConstants";
import * as Styles from "./styles";

interface ForgetConfirmModalProps {
  memoryText: string;
  isBusy: boolean;
  /** Set when the forget failed; nothing was forgotten and the button reads "Try again". */
  errorMessage: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

/**
 * 004 `ForgetDetailConfirm` (FR-21, FR-29). Names the full text. Focus starts
 * on Cancel, since the action is permanent (design §7).
 */
const ForgetConfirmModal = (props: ForgetConfirmModalProps): ReactElement => {
  const { memoryText, isBusy, errorMessage, onCancel, onConfirm } = props;

  return (
    <div className={Styles.modalOverlayStyles}>
      <div className={Styles.modalStyles} role="dialog" aria-modal="true" aria-label="Forget this memory?">
        <div className={Styles.modalBodyStyles}>
          <Eraser size={22} className="shrink-0 text-destructive" />
          <div>
            <div className={Styles.modalTitleStyles}>Forget this memory?</div>
            <div className={Styles.modalMessageStyles}>
              <b className="text-foreground">{memoryText}</b> will be removed for good, and its words
              removed from your capture history. This cannot be undone.
            </div>
            <div className={Styles.modalBackupStyles}>{BACKUP_LINE}</div>
            {errorMessage !== null && (
              <div className={Styles.modalErrorStyles} role="alert">
                {errorMessage}
              </div>
            )}
          </div>
        </div>
        <div className={Styles.modalActionsStyles}>
          <Button autoFocus onClick={onCancel} disabled={isBusy}>
            Cancel
          </Button>
          <BusyButton variant="danger" isBusy={isBusy} busyLabel="Forgetting" onClick={onConfirm}>
            {errorMessage !== null ? "Try again" : "Forget memory"}
          </BusyButton>
        </div>
      </div>
    </div>
  );
};

export default ForgetConfirmModal;
