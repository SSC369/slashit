import { makeAutoObservable } from "mobx";

import type { ExpenseCategory } from "../../types.generated";
import type { ExpensePeriodFragment } from "../api/queries/GetExpensePeriods/responseHandler";
import type { ExpenseFieldsFragment } from "../fragments/ExpenseFields.generated";
import type { ExpenseSummaryFieldsFragment } from "../fragments/ExpenseSummaryFields.generated";

/** FR-17's chips: every expense, or one category. */
export type ExpenseCategoryFilterType = "ALL" | ExpenseCategory;

/** A period is named by its range, so a summary card can pick its period
 * before the picker's list has loaded (sub-plan 4.2, F-10). */
export const periodIdOf = (range: { start: string | null; end: string | null }): string =>
  `${range.start ?? "all"}|${range.end ?? "all"}`;

/**
 * The one copy of every expense the client holds (tech stack §3). The Expenses
 * tab reads `order`; the All tab, capture's saved card and the detail page
 * read by id, so an edit shows everywhere at once.
 */
export class ExpensesStoreModel {
  expenses: Map<string, ExpenseFieldsFragment> = new Map();
  order: string[] = [];
  categoryFilter: ExpenseCategoryFilterType = "ALL";
  /** When the tab last loaded from the server; null until the first load. */
  lastSyncedAt: Date | null = null;
  /** The picker's periods, as the server resolved them (decision 3A). */
  periods: ExpensePeriodFragment[] = [];
  /** The picked period's id; null until a period is picked or loaded. */
  periodId: string | null = null;
  /** The band's totals for the picked period and category. */
  summary: ExpenseSummaryFieldsFragment | null = null;
  /** Whether the account has any expense at all, asked only when a picked
   * period is empty; null until asked. Tells a new user's empty tab from an
   * empty month (`ExpensesStates`, dev log E-6). */
  hasAnyExpense: boolean | null = null;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get(id: string): ExpenseFieldsFragment | null {
    return this.expenses.get(id) ?? null;
  }

  getVisible(): ExpenseFieldsFragment[] {
    return this.order
      .map((id) => this.expenses.get(id))
      .filter((expense): expense is ExpenseFieldsFragment => expense !== undefined);
  }

  setExpenses(expenses: ExpenseFieldsFragment[]): void {
    this.order = expenses.map((expense) => expense.id);
    for (const expense of expenses) {
      this.expenses.set(expense.id, expense);
    }
    this.lastSyncedAt = new Date();
  }

  /** Stores an expense without changing the tab's order; the next load places it. */
  upsert(expense: ExpenseFieldsFragment): void {
    this.expenses.set(expense.id, expense);
  }

  /** Delete (FR-22): the row leaves the tab and every reader at once. */
  remove(id: string): void {
    this.expenses.delete(id);
    this.order = this.order.filter((expenseId) => expenseId !== id);
  }

  setCategoryFilter(filter: ExpenseCategoryFilterType): void {
    this.categoryFilter = filter;
  }

  /** Holds the picker's list. A picked period the list lacks, or none yet,
   * falls back to this month (decision 1A). */
  setPeriods(periods: ExpensePeriodFragment[]): void {
    this.periods = periods;
    const isHeld = periods.some((period) => periodIdOf(period) === this.periodId);
    if (isHeld) return;
    const thisMonth = periods.find((period) => period.key === "THIS_MONTH");
    this.periodId = thisMonth ? periodIdOf(thisMonth) : null;
  }

  selectPeriod(periodId: string): void {
    this.periodId = periodId;
  }

  get selectedPeriod(): ExpensePeriodFragment | null {
    return this.periods.find((period) => periodIdOf(period) === this.periodId) ?? null;
  }

  setSummary(summary: ExpenseSummaryFieldsFragment | null): void {
    this.summary = summary;
  }

  setHasAnyExpense(hasAnyExpense: boolean): void {
    this.hasAnyExpense = hasAnyExpense;
  }

  clear(): void {
    this.expenses.clear();
    this.order = [];
    this.categoryFilter = "ALL";
    this.lastSyncedAt = null;
    this.periods = [];
    this.periodId = null;
    this.summary = null;
    this.hasAnyExpense = null;
  }

  static create(): ExpensesStoreModel {
    return new ExpensesStoreModel();
  }
}
