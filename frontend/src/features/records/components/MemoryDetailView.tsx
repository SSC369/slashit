import { Eraser, Pencil } from "lucide-react";
import type { ReactElement } from "react";

import CategoryTag from "../../../components/CategoryTag";
import Skeleton from "../../../components/Skeleton";
import Button from "../../../design-system/components/Button";
import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import { formatLongDateTime } from "../../../utils/formatDate";
import * as Styles from "./styles";

interface MemoryDetailViewProps {
  memory: MemoryFieldsFragment;
  isOffline: boolean;
  onEdit: () => void;
  onForget: () => void;
}

const isEdited = (memory: MemoryFieldsFragment): boolean => memory.origin === "edit";

/** 004 `MemoryDetail` (FR-17), with Forget (FR-21). */
const MemoryDetailView = (props: MemoryDetailViewProps): ReactElement => {
  const { memory, isOffline, onEdit, onForget } = props;
  return (
    <>
      <div className={Styles.detailTitleStyles}>{memory.text}</div>
      <div className={Styles.detailFieldsStyles}>
        <div className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>Category</div>
          <div className={Styles.detailValueStyles}>
            <CategoryTag category={memory.category} />
          </div>
        </div>
        <div className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>Saved</div>
          <div className={Styles.detailValueStyles}>{formatLongDateTime(memory.createdAt)}</div>
        </div>
        <div className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>Last edited</div>
          <div className={Styles.detailValueStyles}>
            {isEdited(memory) ? formatLongDateTime(memory.updatedAt) : "Never"}
          </div>
        </div>
        <div className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>Origin</div>
          <div className={Styles.detailValueStyles}>Command</div>
        </div>
      </div>
      {memory.originalInput !== null && (
        <div className={Styles.detailInputBlockStyles}>
          <div className={Styles.formLabelStyles}>What you typed</div>
          <div className={Styles.detailInputEchoStyles}>{memory.originalInput}</div>
        </div>
      )}
      <div className={Styles.detailActionsRowStyles}>
        <Button onClick={onEdit} disabled={isOffline}>
          <Pencil size={15} /> Edit
        </Button>
        <Button onClick={onForget} disabled={isOffline}>
          <Eraser size={15} /> Forget
        </Button>
      </div>
    </>
  );
};

export const MemoryDetailSkeleton = (): ReactElement => (
  <div aria-hidden="true">
    <Skeleton width="60%" />
    <div className={Styles.detailFieldsStyles}>
      {[0, 1, 2, 3].map((index) => (
        <div key={index} className={Styles.detailRowStyles}>
          <Skeleton width="40%" />
        </div>
      ))}
    </div>
  </div>
);

export default MemoryDetailView;
