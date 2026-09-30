/**
 * FR-15, mirrored from the backend's `is_question` for one purpose only: the
 * loading card says "Reading your records to answer…" while a question waits.
 * The server decides whether an answer is written; this never does.
 */
const QUESTION_WORDS = new Set([
  "what",
  "when",
  "where",
  "who",
  "why",
  "how",
  "which",
  "do",
  "does",
  "did",
  "is",
  "are",
  "am",
  "have",
  "has",
]);

export const isSearchQuestion = (text: string): boolean => {
  const stripped = text.trim();
  if (stripped.endsWith("?")) return true;
  const firstWord = /^[a-z]+/.exec(stripped.toLowerCase());
  return firstWord !== null && QUESTION_WORDS.has(firstWord[0]);
};
