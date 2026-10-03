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
    case "EXPENSE":
      return `/records/expenses/${row.expense.id}`;
    default: {
      const unhandled: never = row;
      throw new Error(`Unhandled record row: ${JSON.stringify(unhandled)}`);
    }
  }
};

export const recordId = (row: RecordRow): string => {
  switch (row.kind) {
    case "TASK":
      return row.task.id;
    case "REMINDER":
      return row.reminder.id;
    case "MEMORY":
      return row.memory.id;
    case "EVENT":
      return row.event.id;
    case "EXPENSE":
      return row.expense.id;
    default: {
      const unhandled: never = row;
      throw new Error(`Unhandled record row: ${JSON.stringify(unhandled)}`);
    }
  }
};
