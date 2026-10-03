import { Bell, MapPin } from "lucide-react";
import { Fragment, type ReactElement } from "react";

import EventStatusPill from "../../../components/EventStatusPill";
import Skeleton from "../../../components/Skeleton";
import type { EventFieldsFragment } from "../../../fragments/EventFields.generated";
import { cn } from "../../../utils/cn";
import { alertSummary } from "../../../utils/formatEvent";
import * as Styles from "./styles";

const COLUMN_COUNT = 4;
const SKELETON_ROW_COUNT = 2;

interface EventTableProps {
  upcoming: EventFieldsFragment[];
  past: EventFieldsFragment[];
  isLoading: boolean;
  onOpenEvent: (id: string) => void;
}

/** `RecordsEvents` (FR-25, FR-26): upcoming soonest first, then past, most
 * recent first and dimmed. An empty group is left out, not drawn empty. */
const EventTable = (props: EventTableProps): ReactElement => {
  const { upcoming, past, isLoading, onOpenEvent } = props;
  const groups = [
    { label: "Upcoming", events: upcoming },
    { label: "Past", events: past },
  ];
  const total = upcoming.length + past.length;

  return (
    <div className={Styles.cardStyles}>
      <table className={Styles.tableStyles}>
        <thead>
          <tr className={Styles.theadRowStyles}>
            <th className={Styles.thStyles}>Event</th>
            <th className={Styles.thStyles} style={{ width: 260 }}>
              When
            </th>
            <th className={Styles.thStyles} style={{ width: 170 }}>
              Repeat
            </th>
            <th className={Styles.thStyles} style={{ width: 150 }}>
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <>
              <GroupHead label="Upcoming" count={null} />
              {Array.from({ length: SKELETON_ROW_COUNT }, (_, index) => (
                <tr key={index} className={Styles.rowStyles}>
                  <td className={Styles.tdStyles}>
                    <Skeleton width="58%" />
                  </td>
                  <td className={Styles.tdStyles}>
                    <Skeleton width="62%" />
                  </td>
                  <td className={Styles.tdStyles}>
                    <Skeleton width="55%" />
                  </td>
                  <td className={Styles.tdStyles}>
                    <Skeleton width="88px" height={20} />
                  </td>
                </tr>
              ))}
            </>
          ) : (
            groups
              .filter((group) => group.events.length > 0)
              .map((group) => (
                <Fragment key={group.label}>
                  <GroupHead label={group.label} count={group.events.length} />
                  {group.events.map((event) => (
                    <EventRow key={event.id} event={event} onOpenEvent={onOpenEvent} />
                  ))}
                </Fragment>
              ))
          )}
        </tbody>
      </table>
      {!isLoading && (
        <div className={Styles.cardFootStyles}>
          <span>
            {total} {total === 1 ? "event" : "events"}
          </span>
          <span className={Styles.eventFootLegendStyles}>
            Upcoming soonest first · past most recent first · <Bell size={12} /> has an alert
          </span>
        </div>
      )}
    </div>
  );
};

interface EventRowProps {
  event: EventFieldsFragment;
  onOpenEvent: (id: string) => void;
}

/** One tab stop; Enter opens the event (design §7). */
const EventRow = (props: EventRowProps): ReactElement => {
  const { event, onOpenEvent } = props;
  const isPast = event.eventStatus === "PAST";
  const alerts = alertSummary(event.alerts);

  return (
    <tr
      tabIndex={0}
      className={Styles.eventRowStyles}
      onClick={() => onOpenEvent(event.id)}
      onKeyDown={(keyEvent) => {
        if (keyEvent.key === "Enter") onOpenEvent(event.id);
      }}
    >
      <td className={cn(Styles.tdStyles, isPast ? Styles.eventPastTitleCellStyles : Styles.eventTitleCellStyles)}>
        {event.title}
        {alerts !== null && (
          <span className={Styles.eventAlertIconStyles} role="img" aria-label={alerts.spoken}>
            <Bell size={13} />
          </span>
        )}
        {event.location !== null && (
          <div className={Styles.eventMetaStyles}>
            <MapPin size={13} className="shrink-0" />
            {event.location}
          </div>
        )}
      </td>
      <td className={cn(Styles.tdStyles, Styles.secondaryCellStyles)}>{event.whenText}</td>
      <td className={cn(Styles.tdStyles, Styles.dateCellStyles)}>
        {event.repeatYearly ? "Every year" : "Does not repeat"}
      </td>
      <td className={Styles.tdStyles}>
        <EventStatusPill status={event.eventStatus} />
      </td>
    </tr>
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

export default EventTable;
