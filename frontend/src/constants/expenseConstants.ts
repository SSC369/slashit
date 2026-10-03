import type { ExpenseCategory, ExpenseQuestionKind, ExpenseRefusalReason } from "../../types.generated";

/** Mirrors backend/app/domains/expenses/constants.py's MAX_DESCRIPTION_LENGTH (FR-13). */
export const MAX_DESCRIPTION_LENGTH = 200;

/** Mirrors backend capture/constants.py's EXPENSE_CHIP_ANSWER_PREFIX (dev log
 * E-5): a chip answers FR-5's question with this and the candidate's paise, so
 * digits typed anywhere are always read as rupees. */
export const EXPENSE_CHIP_ANSWER_PREFIX = "chip:";

/** One chip's answer: "chip:18000" for ₹180. */
export const chipAnswer = (paise: string): string => `${EXPENSE_CHIP_ANSWER_PREFIX}${paise}`;

/** FR-9's fixed eight, in the order the PRD lists them and the chips draw them. */
export const EXPENSE_CATEGORIES: readonly ExpenseCategory[] = [
  "FOOD",
  "TRANSPORT",
  "SHOPPING",
  "BILLS",
  "HEALTH",
  "ENTERTAINMENT",
  "TRAVEL",
  "OTHER",
];

export const EXPENSE_CATEGORY_LABEL: Record<ExpenseCategory, string> = {
  FOOD: "Food",
  TRANSPORT: "Transport",
  SHOPPING: "Shopping",
  BILLS: "Bills",
  HEALTH: "Health",
  ENTERTAINMENT: "Entertainment",
  TRAVEL: "Travel",
  OTHER: "Other",
};

/** One of FR-3, FR-4, FR-5 or FR-8's questions, with what its card draws. */
export interface ExpenseQuestionArgs {
  pendingCaptureId: string;
  kind: ExpenseQuestionKind;
  question: string;
  /** AMOUNT_CHOICE's chips, in paise, in the order the text names them. */
  amountCandidates: string[];
  /** DATE's reading of the user's phrase, ISO; the calendar opens on it. */
  readDate: string | null;
}

/** FR-6 or FR-13: refused, nothing saved, the typed text kept. */
export interface ExpenseRefusalArgs {
  message: string;
  reason: ExpenseRefusalReason;
  /** The description's length, for DESCRIPTION_TOO_LONG only. */
  length: number | null;
}
