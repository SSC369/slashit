import { IndianRupee } from "lucide-react";
import type { ReactElement } from "react";

import Button from "../../../design-system/components/Button";
import * as Styles from "./styles";

interface EmptyExpensesProps {
  onGoToCapture: () => void;
}

/** `ExpensesStates`, empty: an example command, since the view starts blank. */
const EmptyExpenses = (props: EmptyExpensesProps): ReactElement => {
  const { onGoToCapture } = props;
  return (
    <div className={Styles.noticeCardStyles}>
      <div className={Styles.emptyIconStyles}>
        <IndianRupee size={24} />
      </div>
      <div className={Styles.emptyTitleStyles}>No expenses yet</div>
      <div className={Styles.emptyBodyStyles}>Record one with /add-expense and it appears here, with totals.</div>
      <div className={Styles.emptyExampleStyles}>/add-expense ₹850 dinner yesterday</div>
      <div className={Styles.emptyActionStyles}>
        <Button onClick={onGoToCapture}>Go to Capture</Button>
      </div>
    </div>
  );
};

export default EmptyExpenses;
