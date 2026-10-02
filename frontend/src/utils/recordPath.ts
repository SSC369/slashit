import type { RecordRow } from "../stores/RecordsStore";

/** Where a row of any record type opens its detail. */
export const recordPath = (row: RecordRow): string => {
  switch (row.kind) {
    case "TASK":
      return `/records/${row.task.id}`;
    case "REMINDER":
      return `/records/reminders/${row.reminder.id}`;
    case "MEMORY":
      return `/records/memories/${row.memory.id}`;
    case "EVENT":
      return `/records/events/${row.event.id}`;
    default: {
      const unhandled: never = row;
      throw new Error(`Unhandled record row: ${JSON.stringify(unhandled)}`);
    }
  }
};
