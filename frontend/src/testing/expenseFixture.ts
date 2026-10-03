import type { ExpenseFieldsFragment } from "../fragments/ExpenseFields.generated";
import type { ExpenseSummaryFieldsFragment } from "../fragments/ExpenseSummaryFields.generated";

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

export const buildExpenseSummary = (
  overrides: Partial<ExpenseSummaryFieldsFragment> = {},
): ExpenseSummaryFieldsFragment => ({
  label: "September 2026",
  phrase: "in September 2026",
  start: "2026-09-01",
  end: "2026-09-30",
  count: 42,
  grandTotalPaise: "3845000",
  totals: [
    { category: "FOOD", totalPaise: "1230000" },
    { category: "BILLS", totalPaise: "865000" },
    { category: "ENTERTAINMENT", totalPaise: "120000" },
  ],
  ...overrides,
});
