import { InfoIcon, Pencil, Trash2 } from "lucide-react";
import type { ReactElement } from "react";

import ReminderStatusPill from "../../../components/ReminderStatusPill";
import Skeleton from "../../../components/Skeleton";
import Button from "../../../design-system/components/Button";
import type { ReminderFieldsFragment } from "../../../fragments/ReminderFields.generated";
import { cn } from "../../../utils/cn";
import {
  REMINDER_ACTION_LABEL,
  describeRepeatDetail,
  formatReminderDate,
  formatReminderDateTime,
} from "../../../utils/formatReminder";
import { describeRepeatCadence } from "../../../utils/reminderDraft";
import * as Styles from "./styles";

interface DetailRowProps {
  label: string;
  value: string;
  sub: string | null;
}

const DetailRow = (props: DetailRowProps): ReactElement => {
  const { label, value, sub } = props;
  return (
    <div className={Styles.detailRowStyles}>
      <div className={Styles.detailLabelStyles}>{label}</div>
      <div className={Styles.detailValueStyles}>
        {value}
        {sub !== null && <div className={Styles.detailSubValueStyles}>{sub}</div>}
      </div>
    </div>
  );
};

interface ReminderDetailViewProps {
  reminder: ReminderFieldsFragment;
  isOffline: boolean;
  onEdit: () => void;
  onDelete: () => void;
}

/** `ReminderDetail` (FR-27): every field, and what happened last time. */
const ReminderDetailView = (props: ReminderDetailViewProps): ReactElement => {
  const { reminder, isOffline, onEdit, onDelete } = props;
  const zone = reminder.scheduleTimezone;
  const isRepeating = reminder.repeatKind !== "NONE";

  return (
    <>
      <div className={Styles.detailHeadStyles}>
        <div>
          <div className={Styles.detailTitleStyles}>{reminder.description}</div>
          <div className={Styles.detailPillsStyles}>
            <ReminderStatusPill reminder={reminder} />
            {isRepeating && (
              <span className={cn(Styles.pillBaseStyles, Styles.pillRepeatStyles)}>
                {reminder.repeatText}
              </span>
            )}
          </div>
        </div>
        <div className={Styles.detailActionsInlineStyles}>
          <Button onClick={onEdit} disabled={isOffline}>
            <Pencil size={14} /> Edit
          </Button>
          <Button onClick={onDelete} disabled={isOffline}>
            <Trash2 size={14} /> Delete
          </Button>
        </div>
      </div>

      <div className={Styles.detailFieldsStyles}>
        <DetailRow
          label={reminder.state === "DONE" ? "Finished" : "Next fires"}
          value={reminder.nextFireAt !== null ? reminder.whenText : "Not scheduled"}
          sub={reminder.nextFireAt !== null ? formatReminderDate(reminder.nextFireAt, zone) : null}
        />
        <DetailRow
          label="Repeat"
          value={reminder.repeatText}
          sub={describeRepeatCadence(reminder) ?? (isRepeating ? describeRepeatDetail(reminder) : null)}
        />
        <DetailRow label="Timezone" value={zone} sub="From Settings" />
        <DetailRow
          label="Last fired"
          value={
            reminder.lastFiredAt !== null ? formatReminderDateTime(reminder.lastFiredAt, zone) : "Not yet"
          }
          sub={reminder.lastFiredAt !== null ? formatReminderDate(reminder.lastFiredAt, zone) : null}
        />
        <DetailRow
          label="Then"
          value={reminder.lastAction !== null ? REMINDER_ACTION_LABEL[reminder.lastAction] : "Not yet"}
          sub={null}
        />
        <DetailRow label="Status" value={reminder.state === "DONE" ? "Done" : "Active"} sub={null} />
      </div>

      <div className={Styles.detailMetaStyles}>
        Created {formatReminderDateTime(reminder.createdAt, zone)} · via{" "}
        {reminder.origin === "command" ? "command" : "edit"}
      </div>
      {reminder.originalInput !== null && (
        <div className={Styles.detailInputEchoStyles}>{reminder.originalInput}</div>
      )}

      <div className={cn(Styles.noteInfoStyles, "mt-[22px]")}>
        <InfoIcon size={17} className="shrink-0 text-accent" />
        <div className={Styles.noteInfoTextStyles}>
          Editing changes every future occurrence. A single occurrence cannot be edited on its own.
        </div>
      </div>
    </>
  );
};

/** `ReminderDetailLoading`: skeleton title, pills and field grid. */
export const ReminderDetailSkeleton = (): ReactElement => (
  <div aria-busy="true" aria-label="Loading reminder">
    <Skeleton width="45%" height={24} />
    <div className={Styles.detailPillsStyles}>
      <Skeleton width="84px" height={23} />
      <Skeleton width="112px" height={23} />
    </div>
    <div className={Styles.detailFieldsStyles}>
      {Array.from({ length: 6 }, (_, index) => (
        <div key={index} className={Styles.detailRowStyles}>
          <div className={Styles.detailLabelStyles}>
            <Skeleton width="60%" />
          </div>
          <div className={Styles.detailValueStyles}>
            <Skeleton width="40%" />
          </div>
        </div>
      ))}
    </div>
  </div>
);

export default ReminderDetailView;
