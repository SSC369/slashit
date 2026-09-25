import type { MemoryCategory, SecretKind } from "../../types.generated";
import type { MemoryFieldsFragment } from "../fragments/MemoryFields.generated";

/** Mirrors backend/app/domains/memories/constants.py's MAX_FACT_LENGTH (FR-4). */
export const MAX_FACT_LENGTH = 500;

/** FR-5's fixed four, in the order the design draws them. */
export const MEMORY_CATEGORIES: readonly MemoryCategory[] = [
  "PERSONAL",
  "PEOPLE",
  "PROFESSIONAL",
  "LIFE",
];

export const CATEGORY_LABEL: Record<MemoryCategory, string> = {
  PERSONAL: "Personal",
  PEOPLE: "People",
  PROFESSIONAL: "Professional",
  LIFE: "Life",
};

/** FR-8: the caution names the kind of secret, never the text. */
export const SECRET_CAUTION_TITLE: Record<SecretKind, string> = {
  CARD: "This looks like a card number.",
  ID_NUMBER: "This looks like an ID number.",
  TAX_ID: "This looks like a tax ID.",
  CREDENTIAL: "This looks like a password or PIN.",
};

export const SECRET_CAUTION_BODY =
  "It is saved, and only you can see it. Slashit sends saved text to its AI model when it checks for conflicts, so you may prefer to keep secrets elsewhere.";

/** FR-29. The backup period is set at launch (deferred by the user,
 * 2026-09-25); until then the line states the schedule, not a number. */
export const BACKUP_LINE = "Copies in backups are erased on the regular backup schedule.";

/** Mirrors backend memories/constants.py's FORGET_PICK_LIMIT (sub-plan 4.2, Q2). */
export const FORGET_PICK_LIMIT = 5;

/** What `/forget <which>` offered (FR-24 to FR-27). */
export interface ForgetCandidatesArgs {
  searchText: string;
  candidates: MemoryFieldsFragment[];
  totalMatches: number;
  forgetAll: boolean;
  allCount: number;
}
