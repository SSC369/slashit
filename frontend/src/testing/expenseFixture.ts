import type { ExpenseFieldsFragment } from "../fragments/ExpenseFields.generated";

export const buildExpense = (overrides: Partial<ExpenseFieldsFragment> = {}): ExpenseFieldsFragment => ({
  id: "expense-1",
  amountPaise: "85000",
  description: "Dinner with friends",
  category: "FOOD",
  spentOn: "2026-10-01",
  origin: "command",
  originalInput: "/add-expense ₹850 dinner with friends yesterday",
  createdAt: "2026-10-02T09:41:00+00:00",
  updatedAt: "2026-10-02T09:41:00+00:00",
  ...overrides,
});
