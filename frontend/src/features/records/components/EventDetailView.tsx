import { Bell, InfoIcon, Repeat } from "lucide-react";
import type { ReactElement } from "react";

import EventStatusPill from "../../../components/EventStatusPill";
import Skeleton from "../../../components/Skeleton";
import { EVENT_PAST_DETAIL_NOTE, EVENT_YEARLY_DETAIL_NOTE } from "../../../constants/eventConstants";
import type { EventFieldsFragment } from "../../../fragments/EventFields.generated";
import { cn } from "../../../utils/cn";
import { dayMonth, detailWhen, multiDayLength, timedLength } from "../../../utils/formatEvent";
import { formatReminderDateTime } from "../../../utils/formatReminder";
import * as Styles from "./styles";

interface EventFieldProps {
  label: string;
  /** Null reads "None", dim (design §4 Empty). */
  value: string | null;
  sub: string | null;
}

const EventField = (props: EventFieldProps): ReactElement => {
  const { label, value, sub } = props;
  return (
    <div className={Styles.eventFieldCellStyles}>
      <span className={Styles.formLabelStyles}>{label}</span>
      <span className={cn(Styles.eventFieldValueStyles, value === null && Styles.eventFieldNoneStyles)}>
        {value ?? "None"}
      </span>
      {sub !== null && <span className={Styles.eventFieldSubStyles}>{sub}</span>}
    </div>
  );
};

const whenSub = (event: EventFieldsFragment): string | null => {
  const isSingleAllDay = event.allDay && event.occurrenceEndDate === event.occurrenceDate;
  if (isSingleAllDay) return `All day · stays on ${dayMonth(event.occurrenceDate)} if you change timezone`;
  return multiDayLength(event) ?? timedLength(event);
};

const alertSub = (event: EventFieldsFragment): string | null => {
  if (event.alertFiresAt === null) return null;
  const firesAt = `Fires ${formatReminderDateTime(event.alertFiresAt, event.scheduleTimezone)}`;
  return event.repeatYearly ? `${firesAt} · then every year` : firesAt;
};

interface EventDetailViewProps {
  event: EventFieldsFragment;
}

/** `EventDetail`, `EventDetailTimed`, `EventDetailPast` (FR-27): every field,
 * where it came from, and when its alert fires. Edit and delete are slice 2. */
const EventDetailView = (props: EventDetailViewProps): ReactElement => {
  const { event } = props;
  const isPast = event.eventStatus === "PAST";
  const note = isPast ? EVENT_PAST_DETAIL_NOTE : event.repeatYearly ? EVENT_YEARLY_DETAIL_NOTE : null;

  return (
    <>
      <div className={Styles.detailTitleStyles}>{event.title}</div>
      <div className={cn(Styles.detailPillsStyles, "mb-[22px]")}>
        <EventStatusPill status={event.eventStatus} />
        {event.repeatYearly && (
          <span className={cn(Styles.pillBaseStyles, Styles.pillRepeatStyles)}>
            <Repeat size={12} /> Every year
          </span>
        )}
        {event.alertText !== null && (
          <span className={cn(Styles.pillBaseStyles, Styles.pillAlertStyles)}>
            <Bell size={12} /> Alert
          </span>
        )}
      </div>
      <div className={Styles.cardStyles}>
        <div className={Styles.eventFieldsGridStyles}>
          <EventField
            label={event.repeatYearly && !isPast ? "Next" : "When"}
            value={detailWhen(event)}
            sub={whenSub(event)}
          />
          <EventField
            label="Repeat"
            value={event.repeatYearly ? "Every year" : "Does not repeat"}
            sub={event.repeatYearly ? `On ${dayMonth(event.startDate)}` : null}
          />
          <EventField label="Alert" value={event.alertText} sub={alertSub(event)} />
          <EventField label="Location" value={event.location} sub={null} />
          <EventField label="Description" value={event.eventDescription} sub={null} />
          <EventField label="Timezone" value={event.scheduleTimezone} sub="From Settings" />
        </div>
        <div className={Styles.eventDetailFootStyles}>
          Created {formatReminderDateTime(event.createdAt, event.scheduleTimezone)} · via {event.origin}
          {event.originalInput !== null && (
            <>
              {" "}
              <span className={Styles.eventDetailInputStyles}>{event.originalInput}</span>
            </>
          )}
        </div>
      </div>
      {note !== null && (
        <div className={Styles.eventNoteStyles}>
          <InfoIcon size={16} className="mt-0.5 shrink-0 text-accent" />
          <div>{note}</div>
        </div>
      )}
    </>
  );
};

/** `EventDetailStates` loading. */
export const EventDetailSkeleton = (): ReactElement => (
  <div aria-busy="true" aria-label="Loading event">
    <Skeleton width="45%" height={24} />
    <div className={cn(Styles.detailPillsStyles, "mb-[22px]")}>
      <Skeleton width="84px" height={23} />
    </div>
    <div className={Styles.cardStyles}>
      <div className={Styles.eventFieldsGridStyles}>
        {["When", "Alert", "Location"].map((label) => (
          <div key={label} className={Styles.eventFieldCellStyles}>
            <span className={Styles.formLabelStyles}>{label}</span>
            <Skeleton width="55%" height={12} />
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default EventDetailView;
