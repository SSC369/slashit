export interface CaptureCommand {
  name: string;
  description: string;
}

/**
 * Mirrors backend/app/domains/capture/constants.py's KNOWN_COMMANDS. Used
 * only for the palette's autocomplete; the server is the sole authority on
 * what counts as a known command (an UnrecognisedCommand result is possible
 * even if this list is stale).
 */
export const CAPTURE_COMMANDS: CaptureCommand[] = [
  { name: "/add-task", description: "Create a task" },
  { name: "/tasks", description: "List your open tasks" },
  { name: "/remind", description: "Set a reminder" },
  { name: "/reminders", description: "List your active reminders" },
  { name: "/remember", description: "Save a fact to remember" },
  { name: "/add-memory", description: "Save a fact to remember" },
  { name: "/memories", description: "List or look up your memories" },
  { name: "/forget", description: "Forget a memory for good" },
];

/** Epic 004, FR-1: two names for one action. */
export const MEMORY_SAVE_COMMANDS: readonly string[] = ["/remember", "/add-memory"];

/** Commands that take no argument, so picking one runs it at once. */
export const ARGUMENTLESS_COMMANDS: readonly string[] = ["/tasks", "/reminders", "/memories"];
