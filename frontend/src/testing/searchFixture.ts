import type { SearchResultsFieldsFragment } from "../fragments/SearchResultsFields.generated";
import type { TaskFieldsFragment } from "../fragments/TaskFields.generated";
import { buildMemory } from "./memoryFixture";

export const buildTask = (overrides: Partial<TaskFieldsFragment> = {}): TaskFieldsFragment => ({
  id: "task-1",
  title: "Renew passport",
  dueAt: "2026-10-13T09:00:00+00:00",
  status: "PENDING",
  isOverdue: false,
  origin: "command",
  originalInput: "/add-task Renew passport by 13 Oct",
  createdAt: "2026-09-27T18:12:00+00:00",
  updatedAt: "2026-09-27T18:12:00+00:00",
  ...overrides,
});

/** `SearchPassport`: one memory and one task, both matching "passport". */
export const buildSearchResults = (
  overrides: Partial<SearchResultsFieldsFragment> = {},
): SearchResultsFieldsFragment => ({
  query: "passport",
  meaningUnavailable: false,
  noSupport: false,
  answerUnavailable: false,
  answer: null,
  groups: [
    {
      recordType: "MEMORY",
      total: 1,
      hits: [{ citation: null, record: { __typename: "Memory", ...buildMemory() } }],
    },
    {
      recordType: "TASK",
      total: 1,
      hits: [{ citation: null, record: { __typename: "Task", ...buildTask() } }],
    },
  ],
  ...overrides,
});

/** `Main`: the passport question, answered from the memory [1] and the task [2]. */
export const buildAnsweredResults = (
  overrides: Partial<SearchResultsFieldsFragment> = {},
): SearchResultsFieldsFragment =>
  buildSearchResults({
    query: "when does my passport expire?",
    answer: {
      sentences: [
        { text: "Your passport expires in 2030.", citations: [1] },
        { text: "You also have a pending task to renew it.", citations: [2] },
      ],
    },
    groups: [
      {
        recordType: "MEMORY",
        total: 1,
        hits: [{ citation: 1, record: { __typename: "Memory", ...buildMemory() } }],
      },
      {
        recordType: "TASK",
        total: 1,
        hits: [{ citation: 2, record: { __typename: "Task", ...buildTask() } }],
      },
    ],
    ...overrides,
  });
