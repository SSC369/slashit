import { Fragment, useState, type ReactElement } from "react";

import ReminderStatusPill from "../../../components/ReminderStatusPill";
import Skeleton from "../../../components/Skeleton";
import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import { cn } from "../../../utils/cn";
import * as Styles from "./styles";

/** Done rows shown before "Show N more done", as `Main` draws it. */
const DONE_PREVIEW_COUNT = 1;
const SKELETON_ROWS_PER_GROUP = 2;
const COLUMN_COUNT = 4;

interface ReminderGroupView {
  label: string;
  reminders: ReminderFieldsFragment[];
}

interface ReminderTableProps {
  needsAttention: ReminderFieldsFragment[];
  upcoming: ReminderFieldsFragment[];
  done: ReminderFieldsFragment[];
  isLoading: boolean;
  footLeft: string;
  onOpenReminder: (id: string) => void;
}

/** `Main` and `RecordsLoading`: the Reminders tab, grouped so what needs
 * attention is read first. An empty group is left out, not drawn empty. */
const ReminderTable = (props: ReminderTableProps): ReactElement => {
  const { needsAttention, upcoming, done, isLoading, footLeft, onOpenReminder } = props;
  const [isDoneExpanded, setIsDoneExpanded] = useState(false);

  const hiddenDoneCount = isDoneExpanded ? 0 : Math.max(done.length - DONE_PREVIEW_COUNT, 0);
  const visibleDone = hiddenDoneCount > 0 ? done.slice(0, DONE_PREVIEW_COUNT) : done;
  const groups: ReminderGroupView[] = [
    { label: "Needs attention", reminders: needsAttention },
    { label: "Upcoming", reminders: upcoming },
    { label: "Done", reminders: visibleDone },
  ];

  return (
    <div className={Styles.cardStyles}>
      <table className={Styles.tableStyles}>
        <thead>
          <tr className={Styles.theadRowStyles}>
            <th className={Styles.thStyles}>Reminder</th>
            <th className={Styles.thStyles} style={{ width: 230 }}>
              Next or fired
            </th>
            <th className={Styles.thStyles} style={{ width: 200 }}>
              Repeat
            </th>
            <th className={Styles.thStyles} style={{ width: 160 }}>
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          {isLoading
            ? groups.map((group) => (
                <Fragment key={group.label}>
                  <GroupHead label={group.label} count={null} />
                  {Array.from({ length: SKELETON_ROWS_PER_GROUP }, (_, index) => (
                    <tr key={index} className={Styles.rowStyles}>
                      <td className={Styles.tdStyles}>
                        <Skeleton width="45%" />
                      </td>
                      <td className={Styles.tdStyles}>
                        <Skeleton width="70%" />
                      </td>
                      <td className={Styles.tdStyles}>
                        <Skeleton width="60%" />
                      </td>
                      <td className={Styles.tdStyles}>
                        <Skeleton width="50%" />
                      </td>
                    </tr>
                  ))}
                </Fragment>
              ))
            : groups
                .filter((group) => group.reminders.length > 0)
                .map((group) => (
                  <Fragment key={group.label}>
                    <GroupHead
                      label={group.label}
                      count={group.label === "Done" ? done.length : group.reminders.length}
                    />
                    {group.reminders.map((reminder) => (
                      <tr
                        key={reminder.id}
                        className={Styles.rowStyles}
                        onClick={() => onOpenReminder(reminder.id)}
                      >
                        <td
                          className={cn(
                            Styles.tdStyles,
                            reminder.state === "DONE"
                              ? Styles.titleDoneCellStyles
                              : Styles.titleCellStyles,
                          )}
                        >
                          {reminder.description}
                        </td>
                        <td className={cn(Styles.tdStyles, Styles.secondaryCellStyles)}>
                          {reminder.whenText}
                        </td>
                        <td className={cn(Styles.tdStyles, Styles.secondaryCellStyles)}>
                          {reminder.repeatText}
                        </td>
                        <td className={Styles.tdStyles}>
                          <ReminderStatusPill reminder={reminder} />
                        </td>
                      </tr>
                    ))}
                  </Fragment>
                ))}
          {!isLoading && hiddenDoneCount > 0 && (
            <tr>
              <td colSpan={COLUMN_COUNT} className={Styles.groupHeadCellStyles}>
                <button
                  type="button"
                  className={Styles.showMoreCellStyles}
                  onClick={() => setIsDoneExpanded(true)}
                >
                  Show {hiddenDoneCount} more done
                </button>
              </td>
            </tr>
          )}
        </tbody>
      </table>
      {!isLoading && (
        <div className={Styles.cardFootStyles}>
          <span>{footLeft}</span>
          <span>Every record here was created by a command</span>
        </div>
      )}
    </div>
  );
};

interface GroupHeadProps {
  label: string;
  /** Null while loading: the header is real, the count is not known yet. */
  count: number | null;
}

const GroupHead = (props: GroupHeadProps): ReactElement => {
  const { label, count } = props;
  return (
    <tr>
      <td colSpan={COLUMN_COUNT} className={Styles.groupHeadCellStyles}>
        <div className={Styles.groupHeadStyles}>
          <span>{label}</span>
          {count !== null && <span className={Styles.groupCountStyles}>{count}</span>}
        </div>
      </td>
    </tr>
  );
};

export default ReminderTable;
