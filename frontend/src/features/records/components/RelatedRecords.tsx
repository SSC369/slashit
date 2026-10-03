import type { KeyboardEvent, ReactElement } from "react";

import CategoryTag from "../../../components/CategoryTag";
import EventMarker from "../../../components/EventMarker";
import ExpenseMarker from "../../../components/ExpenseMarker";
import EventStatusPill from "../../../components/EventStatusPill";
import ReminderStatusPill from "../../../components/ReminderStatusPill";
import Button from "../../../design-system/components/Button";
import type { RecordRow } from "../../../stores/RecordsStore";
import { cn } from "../../../utils/cn";
import { formatShortDate } from "../../../utils/formatDate";
import { formatEventStart } from "../../../utils/formatEvent";
import { formatDayShort } from "../../../utils/localDate";
import { formatRupees } from "../../../utils/money";
import { recordId } from "../../../utils/recordPath";
import * as Styles from "./styles";

const SKELETON_ROW_COUNT = 3;

export type RelatedStateType = "LOADING" | "ERROR" | "EMPTY" | "LIST";

interface RelatedRecordsProps {
  state: RelatedStateType;
  rows: RecordRow[];
  onOpenRow: (row: RecordRow, position: number) => void;
  onRetry: () => void;
}

/**
 * Epic 005, `RelatedDetail` and `RelatedStates` (FR-25 to FR-28): up to five
 * records close in meaning, under a detail's fields. Its own states never
 * touch the detail above it.
 */
const RelatedRecords = (props: RelatedRecordsProps): ReactElement => {
  const { state, rows, onOpenRow, onRetry } = props;

  return (
    <section
      aria-label="Related records"
      aria-busy={state === "LOADING"}
      className={Styles.relatedSectionStyles}
    >
      <div className={Styles.relatedHeadStyles}>
        <div className={Styles.relatedLabelStyles}>Related</div>
        <span className={Styles.relatedWhyStyles}>Found by meaning · not links you made</span>
      </div>
      <RelatedBody state={state} rows={rows} onOpenRow={onOpenRow} onRetry={onRetry} />
    </section>
  );
};

const RelatedBody = (props: RelatedRecordsProps): ReactElement => {
  const { state, rows, onOpenRow, onRetry } = props;

  switch (state) {
    case "LOADING":
      return (
        <div>
          {Array.from({ length: SKELETON_ROW_COUNT }, (_, index) => (
            <div key={index} className={Styles.relatedRowStyles}>
              <div className={Styles.skeletonBlockStyles} style={{ width: `${60 - index * 8}%` }} />
            </div>
          ))}
        </div>
      );
    case "ERROR":
      return (
        <div className={Styles.relatedErrorStyles} role="status">
          <span>Related records could not be loaded.</span>
          <Button size="sm" onClick={onRetry}>
            Try again
          </Button>
        </div>
      );
    case "EMPTY":
      return (
        <div className={Styles.relatedEmptyStyles}>
          <div>Nothing related yet</div>
          <div className={Styles.relatedEmptyBodyStyles}>
            As you record more, records close in meaning to this one appear here.
          </div>
        </div>
      );
    case "LIST":
      return (
        <div>
          {rows.map((row, index) => (
            <RelatedRow key={recordId(row)} row={row} onOpen={() => onOpenRow(row, index + 1)} />
          ))}
        </div>
      );
    default: {
      const unhandled: never = state;
      throw new Error(`Unhandled related state: ${String(unhandled)}`);
    }
  }
};

const RelatedRow = (props: { row: RecordRow; onOpen: () => void }): ReactElement => {
  const { row, onOpen } = props;
  const openOnEnter = (event: KeyboardEvent<HTMLDivElement>): void => {
    if (event.key === "Enter") onOpen();
  };

  return (
    <div role="button" tabIndex={0} className={Styles.relatedRowStyles} onClick={onOpen} onKeyDown={openOnEnter}>
      <RelatedCells row={row} />
    </div>
  );
};

const RelatedCells = (props: { row: RecordRow }): ReactElement => {
  const { row } = props;

  switch (row.kind) {
    case "TASK": {
      const isDone = row.task.status === "done";
      return (
        <>
          <span className={Styles.relatedTypeStyles}>
            <span className={Styles.typeDotStyles} />
            Task
          </span>
          <span className={Styles.relatedTitleStyles}>{row.task.title}</span>
          <span className={Styles.relatedDateStyles}>{formatShortDate(row.task.dueAt)}</span>
          <span className={Styles.relatedStatusStyles}>
            <span className={cn(Styles.pillBaseStyles, isDone ? Styles.pillDoneStyles : Styles.pillPendingStyles)}>
              {isDone ? "Done" : "Pending"}
            </span>
          </span>
        </>
      );
    }
    case "REMINDER":
      return (
        <>
          <span className={Styles.relatedTypeStyles}>
            <span className={Styles.typeDotReminderStyles} />
            Reminder
          </span>
          <span className={Styles.relatedTitleStyles}>{row.reminder.description}</span>
          <span className={Styles.relatedDateStyles}>{row.reminder.whenText}</span>
          <span className={Styles.relatedStatusStyles}>
            <ReminderStatusPill reminder={row.reminder} />
          </span>
        </>
      );
    case "MEMORY":
      return (
        <>
          <span className={Styles.relatedTypeStyles}>
            <span className={Styles.typeDotMemoryStyles} />
            Memory
          </span>
          <span className={Styles.relatedTitleStyles}>{row.memory.text}</span>
          <span className={Styles.relatedDateStyles}>{formatShortDate(row.memory.createdAt)}</span>
          <span className={Styles.relatedStatusStyles}>
            <CategoryTag category={row.memory.category} />
          </span>
        </>
      );
    case "EVENT":
      return (
        <>
          <span className={Styles.relatedTypeStyles}>
            <EventMarker />
            Event
          </span>
          <span className={Styles.relatedTitleStyles}>{row.event.title}</span>
          <span className={Styles.relatedDateStyles}>{formatEventStart(row.event)}</span>
          <span className={Styles.relatedStatusStyles}>
            <EventStatusPill status={row.event.eventStatus} />
          </span>
        </>
      );
    case "EXPENSE":
      return (
        <>
          <span className={Styles.relatedTypeStyles}>
            <ExpenseMarker />
            Expense
          </span>
          <span className={Styles.relatedTitleStyles}>{row.expense.description}</span>
          <span className={Styles.relatedDateStyles}>{formatDayShort(row.expense.spentOn)}</span>
          <span className={cn(Styles.relatedStatusStyles, Styles.amountStyles)}>
            {formatRupees(row.expense.amountPaise)}
          </span>
        </>
      );
  }
};

export default RelatedRecords;
