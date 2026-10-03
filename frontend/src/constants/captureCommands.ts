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
  // Epic 005, FR-1: first, as `SearchDiscovery` draws it.
  { name: "/search", description: "Search everything you have recorded" },
  { name: "/add-task", description: "Create a task" },
  { name: "/tasks", description: "List your open tasks" },
  { name: "/remind", description: "Set a reminder" },
  { name: "/reminders", description: "List your active reminders" },
  { name: "/remember", description: "Save a fact to remember" },
  { name: "/add-memory", description: "Save a fact to remember" },
  { name: "/memories", description: "List or look up your memories" },
  // Epic 007, design §8.
  { name: "/add-event", description: "Create an event" },
  { name: "/events", description: "List your upcoming events" },
  { name: "/add-expense", description: "Record an expense" },
  { name: "/expenses", description: "Totals by category for a period" },
];

/** Epic 004, FR-1: two names for one action. */
export const MEMORY_SAVE_COMMANDS: readonly string[] = ["/remember", "/add-memory"];

/** Commands that take no argument, so picking one runs it at once. */
export const ARGUMENTLESS_COMMANDS: readonly string[] = ["/tasks", "/reminders", "/memories", "/events"];
