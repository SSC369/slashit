import type { MemoryCategory, SecretKind } from "../../types.generated";

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
