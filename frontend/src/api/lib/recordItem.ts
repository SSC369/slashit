import type { RecordItem } from "../queries/GetRecords/responseHandler";
import type { ExpenseRecordFieldsFragment } from "../../fragments/ExpenseRecordFields.generated";

/** A record as a union selection returns it: an expense with D-11's aliases. */
export type ListedRecord =
  | Exclude<RecordItem, { __typename: "Expense" }>
  | ({ __typename: "Expense" } & ExpenseRecordFieldsFragment);

/** Undoes `ExpenseRecordFields`' aliases, so an expense here matches
 * ExpenseFields wherever it is stored. */
export const toRecordItem = (item: ListedRecord): RecordItem => {
  if (item.__typename !== "Expense") return item;
  const { expenseCategory, expenseOriginalInput, ...rest } = item;
  return { ...rest, category: expenseCategory, originalInput: expenseOriginalInput };
};
