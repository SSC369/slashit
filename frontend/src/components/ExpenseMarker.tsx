import { IndianRupee } from "lucide-react";
import type { ReactElement } from "react";

import * as Styles from "./styles";

/** 006 design change 2026-10-03: a ₹ marks an expense among other record
 * types, where 007's diamond marks an event. Matches capture history's icon. */
const ExpenseMarker = (): ReactElement => (
  <IndianRupee role="img" aria-label="Expense" size={12} strokeWidth={2.5} className={Styles.expenseMarkerStyles} />
);

export default ExpenseMarker;
