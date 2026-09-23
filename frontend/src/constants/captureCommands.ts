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
];

/** Commands that take no argument, so picking one runs it at once. */
export const ARGUMENTLESS_COMMANDS: readonly string[] = ["/tasks", "/reminders"];
