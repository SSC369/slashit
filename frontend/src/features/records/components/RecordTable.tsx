import type { ReactElement } from "react";

import ReminderStatusPill from "../../../components/ReminderStatusPill";
import type { RecordRow } from "../../../stores/RecordsStore";
import { cn } from "../../../utils/cn";
import { formatShortDate } from "../../../utils/formatDate";
import * as Styles from "./styles";

interface RecordTableProps {
  records: RecordRow[];
  onOpenRecord: (row: RecordRow) => void;
  isLoading?: boolean;
}

const SKELETON_ROW_COUNT = 4;

const RecordTable = (props: RecordTableProps): ReactElement => {
  const { records, onOpenRecord, isLoading = false } = props;

  if (isLoading) {
    return (
      <div className={Styles.cardStyles}>
        <table className={Styles.tableStyles}>
          <thead>
            <tr className={Styles.theadRowStyles}>
              <th className={Styles.thStyles} style={{ width: 112 }}>
                Type
              </th>
              <th className={Styles.thStyles}>Title</th>
              <th className={Styles.thStyles} style={{ width: 180 }}>
                Date
              </th>
              <th className={Styles.thStyles} style={{ width: 150 }}>
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: SKELETON_ROW_COUNT }, (_, index) => (
              <tr key={index} className={Styles.rowStyles}>
                <td className={Styles.tdStyles}>
                  <div className={Styles.skeletonBlockStyles} style={{ width: "60%" }} />
                </td>
                <td className={Styles.tdStyles}>
                  <div className={Styles.skeletonBlockStyles} style={{ width: "45%" }} />
                </td>
                <td className={Styles.tdStyles}>
                  <div className={Styles.skeletonBlockStyles} style={{ width: "70%" }} />
                </td>
                <td className={Styles.tdStyles}>
                  <div className={Styles.skeletonBlockStyles} style={{ width: "55%" }} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  const hasReminders = records.some((row) => row.kind === "REMINDER");

  return (
    <div className={Styles.cardStyles}>
      <table className={Styles.tableStyles}>
        <thead>
          <tr className={Styles.theadRowStyles}>
            <th className={Styles.thStyles} style={{ width: 112 }}>
              Type
            </th>
            <th className={Styles.thStyles}>Title</th>
            <th className={Styles.thStyles} style={{ width: 180 }}>
              Date
            </th>
            <th className={Styles.thStyles} style={{ width: 150 }}>
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          {records.map((row) =>
            row.kind === "TASK" ? (
              <TaskRow key={row.task.id} row={row} onOpenRecord={onOpenRecord} />
            ) : (
              <ReminderRow key={row.reminder.id} row={row} onOpenRecord={onOpenRecord} />
            ),
          )}
        </tbody>
      </table>
      <div className={Styles.cardFootStyles}>
        <span>
          {records.length} {records.length === 1 ? "record" : "records"}
        </span>
        <span>
          {hasReminders
            ? "Reminders carry a round marker, tasks a square one"
            : "Every record here was created by a command"}
        </span>
      </div>
    </div>
  );
};

interface TaskRowProps {
  row: Extract<RecordRow, { kind: "TASK" }>;
  onOpenRecord: (row: RecordRow) => void;
}

const TaskRow = (props: TaskRowProps): ReactElement => {
  const { row, onOpenRecord } = props;
  const { task } = row;
  const isDone = task.status === "done";
  return (
    <tr className={Styles.rowStyles} onClick={() => onOpenRecord(row)}>
      <td className={Styles.tdStyles}>
        <span className={Styles.typeTagStyles}>
          <span className={Styles.typeDotStyles} />
          Task
        </span>
      </td>
      <td className={cn(Styles.tdStyles, isDone ? Styles.titleDoneCellStyles : Styles.titleCellStyles)}>
        {task.title}
      </td>
      <td className={cn(Styles.tdStyles, Styles.dateCellStyles)}>{formatShortDate(task.dueAt)}</td>
      <td className={Styles.tdStyles}>
        <span
          className={cn(Styles.pillBaseStyles, isDone ? Styles.pillDoneStyles : Styles.pillPendingStyles)}
        >
          {isDone ? "Done" : "Pending"}
        </span>
      </td>
    </tr>
  );
};

interface ReminderRowProps {
  row: Extract<RecordRow, { kind: "REMINDER" }>;
  onOpenRecord: (row: RecordRow) => void;
}

/** `RecordsAll`: a reminder beside tasks, told apart by its round marker. */
const ReminderRow = (props: ReminderRowProps): ReactElement => {
  const { row, onOpenRecord } = props;
  const { reminder } = row;
  const isDone = reminder.state === "DONE";
  return (
    <tr className={Styles.rowStyles} onClick={() => onOpenRecord(row)}>
      <td className={Styles.tdStyles}>
        <span className={Styles.typeTagStyles}>
          <span className={Styles.typeDotReminderStyles} />
          Reminder
        </span>
      </td>
      <td className={cn(Styles.tdStyles, isDone ? Styles.titleDoneCellStyles : Styles.titleCellStyles)}>
        {reminder.description}
      </td>
      <td className={cn(Styles.tdStyles, Styles.dateCellStyles)}>{reminder.whenText}</td>
      <td className={Styles.tdStyles}>
        <ReminderStatusPill reminder={reminder} />
      </td>
    </tr>
  );
};

export default RecordTable;
