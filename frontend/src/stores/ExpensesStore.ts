import { makeAutoObservable } from "mobx";

import type { ExpenseCategory } from "../../types.generated";
import type { ExpenseFieldsFragment } from "../fragments/ExpenseFields.generated";

/** FR-17's chips: every expense, or one category. */
export type ExpenseCategoryFilterType = "ALL" | ExpenseCategory;

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

  clear(): void {
    this.expenses.clear();
    this.order = [];
    this.categoryFilter = "ALL";
    this.lastSyncedAt = null;
  }

  static create(): ExpensesStoreModel {
    return new ExpensesStoreModel();
  }
}
