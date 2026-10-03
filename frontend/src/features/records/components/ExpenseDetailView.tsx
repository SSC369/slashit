import { Pencil, Trash2 } from "lucide-react";
import type { ReactElement } from "react";

import ExpenseCategoryTag from "../../../components/ExpenseCategoryTag";
import Skeleton from "../../../components/Skeleton";
import Button from "../../../design-system/components/Button";
import type { ExpenseFieldsFragment } from "../../../fragments/ExpenseFields.generated";
import { formatLongDateTime } from "../../../utils/formatDate";
import { formatDayLong } from "../../../utils/localDate";
import { formatRupees, spokenRupees } from "../../../utils/money";
import * as Styles from "./styles";

interface ExpenseDetailViewProps {
  expense: ExpenseFieldsFragment;
  isOffline: boolean;
  onEdit: () => void;
  onDelete: () => void;
}

/** Saved and last changed in the same write, so equal means never edited. */
const isEdited = (expense: ExpenseFieldsFragment): boolean => expense.updatedAt !== expense.createdAt;

/** `ExpenseDetail` (FR-20): the amount as headline, then every field. */
const ExpenseDetailView = (props: ExpenseDetailViewProps): ReactElement => {
  const { expense, isOffline, onEdit, onDelete } = props;
  return (
    <>
      <div className={Styles.expenseDetailAmountStyles} aria-label={spokenRupees(expense.amountPaise)}>
        {formatRupees(expense.amountPaise)}
      </div>
      <div className={Styles.expenseDetailDescriptionStyles}>{expense.description}</div>
      <div className={Styles.detailFieldsStyles}>
        <div className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>Category</div>
          <div className={Styles.detailValueStyles}>
            <ExpenseCategoryTag category={expense.category} />
          </div>
        </div>
        <div className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>Date</div>
          <div className={Styles.detailValueStyles}>{formatDayLong(expense.spentOn)}</div>
        </div>
        <div className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>Saved</div>
          <div className={Styles.detailValueStyles}>{formatLongDateTime(expense.createdAt)}</div>
        </div>
        <div className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>Last edited</div>
          <div className={Styles.detailValueStyles}>
            {isEdited(expense) ? formatLongDateTime(expense.updatedAt) : "Never"}
          </div>
        </div>
        <div className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>Origin</div>
          <div className={Styles.detailValueStyles}>Command</div>
        </div>
      </div>
      <div className={Styles.detailInputBlockStyles}>
        <div className={Styles.formLabelStyles}>What you typed</div>
        <div className={Styles.detailInputEchoStyles}>{expense.originalInput}</div>
      </div>
      <div className={Styles.detailActionsRowStyles}>
        <Button onClick={onEdit} disabled={isOffline}>
          <Pencil size={15} /> Edit
        </Button>
        <Button className={Styles.deleteButtonStyles} onClick={onDelete} disabled={isOffline}>
          <Trash2 size={15} /> Delete
        </Button>
      </div>
    </>
  );
};

/** `DetailStates`, loading. */
export const ExpenseDetailSkeleton = (): ReactElement => (
  <div aria-hidden="true">
    <Skeleton width="120px" height={26} />
    <div className={Styles.detailFieldsStyles}>
      {[0, 1, 2, 3].map((index) => (
        <div key={index} className={Styles.detailRowStyles}>
          <Skeleton width="40%" />
        </div>
      ))}
    </div>
  </div>
);

export default ExpenseDetailView;
