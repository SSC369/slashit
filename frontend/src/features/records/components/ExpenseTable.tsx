import type { ReactElement } from "react";

import ExpenseCategoryTag from "../../../components/ExpenseCategoryTag";
import type { ExpenseFieldsFragment } from "../../../fragments/ExpenseFields.generated";
import { cn } from "../../../utils/cn";
import { formatDayShort } from "../../../utils/localDate";
import { formatRupees, spokenRupees } from "../../../utils/money";
import * as Styles from "./styles";

interface ExpenseTableProps {
  expenses: ExpenseFieldsFragment[];
  isLoading: boolean;
  onOpenExpense: (id: string) => void;
}

const SKELETON_ROW_COUNT = 3;

/** `RecordsExpenses` (FR-16): date, description, category, amount, newest first. */
const ExpenseTable = (props: ExpenseTableProps): ReactElement => {
  const { expenses, isLoading, onOpenExpense } = props;
  const count = expenses.length;

  return (
    <div className={Styles.cardStyles}>
      <table className={Styles.tableStyles}>
        <thead>
          <tr className={Styles.theadRowStyles}>
            <th className={Styles.thStyles} style={{ width: 150 }}>
              Date
            </th>
            <th className={Styles.thStyles}>Description</th>
            <th className={Styles.thStyles} style={{ width: 170 }}>
              Category
            </th>
            <th className={cn(Styles.thStyles, Styles.amountHeadStyles)} style={{ width: 150 }}>
              Amount
            </th>
          </tr>
        </thead>
        <tbody>
          {isLoading
            ? Array.from({ length: SKELETON_ROW_COUNT }, (_, index) => (
                <tr key={index} className={Styles.rowStyles} aria-hidden="true">
                  <td className={Styles.tdStyles}>
                    <div className={Styles.skeletonBlockStyles} style={{ width: 70 }} />
                  </td>
                  <td className={Styles.tdStyles}>
                    <div className={Styles.skeletonBlockStyles} style={{ width: "55%" }} />
                  </td>
                  <td className={Styles.tdStyles}>
                    <div className={Styles.skeletonBlockStyles} style={{ width: "50%" }} />
                  </td>
                  <td className={Styles.tdStyles}>
                    <div className={cn(Styles.skeletonBlockStyles, "ml-auto")} style={{ width: 60 }} />
                  </td>
                </tr>
              ))
            : expenses.map((expense) => (
                <tr key={expense.id} className={Styles.rowStyles} onClick={() => onOpenExpense(expense.id)}>
                  <td className={cn(Styles.tdStyles, Styles.dateCellStyles)}>{formatDayShort(expense.spentOn)}</td>
                  <td className={cn(Styles.tdStyles, Styles.expenseDescriptionCellStyles)}>
                    {expense.description}
                  </td>
                  <td className={Styles.tdStyles}>
                    <ExpenseCategoryTag category={expense.category} />
                  </td>
                  <td
                    className={cn(Styles.tdStyles, Styles.amountCellStyles)}
                    aria-label={spokenRupees(expense.amountPaise)}
                  >
                    {formatRupees(expense.amountPaise)}
                  </td>
                </tr>
              ))}
        </tbody>
      </table>
      {!isLoading && (
        <div className={Styles.cardFootStyles}>
          <span>
            {count} {count === 1 ? "expense" : "expenses"} · newest first
          </span>
          <span>Only you can see these</span>
        </div>
      )}
    </div>
  );
};

export default ExpenseTable;
