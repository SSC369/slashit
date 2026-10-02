import type { ReactElement } from "react";

import { EXPENSE_CATEGORY_LABEL } from "../constants/expenseConstants";
import type { ExpenseCategory } from "../../types.generated";
import * as Styles from "./styles";

interface ExpenseCategoryTagProps {
  category: ExpenseCategory;
}

/** 004's `.cat`, reused: every expense has one of the eight (FR-10). */
export const ExpenseCategoryTag = (props: ExpenseCategoryTagProps): ReactElement => {
  const { category } = props;
  return <span className={Styles.categoryTagStyles}>{EXPENSE_CATEGORY_LABEL[category]}</span>;
};

export default ExpenseCategoryTag;
