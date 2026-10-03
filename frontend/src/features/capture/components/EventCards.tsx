import { AlertCircle, ArrowRight, Bell, CalendarDays, Check, MapPin, Repeat } from "lucide-react";
import { Fragment, type ReactElement } from "react";

import EventStatusPill from "../../../components/EventStatusPill";
import InlineSpinner from "../../../components/InlineSpinner";
import Skeleton from "../../../components/Skeleton";
import Button from "../../../design-system/components/Button";
import {
  EVENT_EXAMPLE_COMMAND,
  EVENT_LIMIT_BODY,
  EVENT_LIMIT_TITLE,
  MAX_ACTIVE_REMINDERS,
  REPEAT_NOTE_PREFIX,
  type EventAlertNotSet,
} from "../../../constants/eventConstants";
import type { EventFieldsFragment } from "../../../fragments/EventFields.generated";
import {
  alertFireText,
  alertSummary,
  dateBoxParts,
  leadDate,
  monthHeading,
  multiDayLength,
} from "../../../utils/formatEvent";
import * as Styles from "./styles";

const FIELDS_PER_ROW = 3;

interface EventFieldView {
  label: string;
  value: string;
  note: string | null;
}

/** The confirmation's fields (design §8): every resolved value, with the
 * server's note under the field it explains. A past event shows its status
 * where a repeat would go (`EventResolvedMore`). */
const savedFields = (event: EventFieldsFragment): EventFieldView[] => {
  const repeatNote = event.whenNotes.find((note) => note.startsWith(REPEAT_NOTE_PREFIX)) ?? null;
  const whenNote =
    event.whenNotes.find((note) => !note.startsWith(REPEAT_NOTE_PREFIX)) ?? multiDayLength(event);
  const fields: EventFieldView[] = [
    { label: "Event", value: event.title, note: null },
    { label: "When", value: event.whenText, note: whenNote },
  ];
  if (event.location !== null) fields.push({ label: "Location", value: event.location, note: null });
  if (event.eventStatus === "PAST") {
    fields.push({ label: "Status", value: "Past", note: "Kept in Records, not listed by /events" });
  } else {
    fields.push({
      label: "Repeat",
      value: event.repeatYearly ? "Every year" : "Does not repeat",
      note: repeatNote,
    });
  }
  return fields;
};

interface AlertLineView {
  key: string;
  lead: string;
  note: string;
  isSet: boolean;
}

/** The Alerts field (`EventAlerts`, `EventAlertsPassed`, `EventAlertsCap`):
 * each alert set, soonest first, with when it fires, then each one not set. */
const alertLines = (event: EventFieldsFragment, alertsNotSet: EventAlertNotSet[]): AlertLineView[] => [
  ...event.alerts.map((alert) => ({
    key: `set-${alert.leadMinutes}`,
    lead: alert.text,
    note: alertFireText(alert, event),
    isSet: true,
  })),
  ...alertsNotSet.map((alert) => ({
    key: `not-set-${alert.leadMinutes}`,
    lead: alert.text,
    note: "Not set",
    isSet: false,
  })),
];

/** Design §8's notes under the Alerts field: a lead named twice, and an
 * all-day event's alerts at the default reminder time (FR-15, FR-34). */
const alertFieldNotes = (event: EventFieldsFragment): string[] => [
  ...event.alertNotes,
  ...(event.allDay && event.alerts.length > 0 ? ["At your default reminder time"] : []),
];

const capitalised = (text: string): string => text.charAt(0).toUpperCase() + text.slice(1);

/** Design §8, "Alert passed", "Reminder cap", "Some alerts not set" and
 * "Some alerts over the cap". */
const alertsNotSetCopy = (
  event: EventFieldsFragment,
  alertsNotSet: EventAlertNotSet[],
): { title: string; body: string } => {
  const askedCount = event.alerts.length + alertsNotSet.length;
  const notSetCount = alertsNotSet.length;
  const isOnlyAlert = askedCount === 1;
  const passedSentences = alertsNotSet
    .filter((alert) => alert.reason === "PASSED")
    .map(
      (alert) =>
        `${capitalised(alert.text)} is ${leadDate(event, alert.leadMinutes)}, which has already passed.`,
    );
  const overCapLeads = alertsNotSet.filter((alert) => alert.reason === "CAP").map((alert) => alert.text);
  const capPrefix = `You have ${MAX_ACTIVE_REMINDERS} active reminders and alerts, the most Slashit holds.`;
  const sentences = [...passedSentences];
  if (isOnlyAlert && overCapLeads.length > 0) {
    sentences.push(`${capPrefix} Mark a reminder done or remove an alert, then add it here.`);
  } else if (overCapLeads.length > 0) {
    sentences.push(
      `${capPrefix} The alerts that fire first were set. Free one up, then add ${overCapLeads.join(" and ")} in Edit.`,
    );
  } else if (isOnlyAlert) {
    sentences.push("Edit the event to choose a later alert.");
  } else if (event.alerts.length > 0) {
    sentences.push(event.alerts.length === 1 ? "The other alert is set." : "The other alerts are set.");
  }
  const title = isOnlyAlert
    ? "The alert was not set"
    : `${notSetCount} of ${askedCount} alerts ${notSetCount === 1 ? "was" : "were"} not set`;
  return { title, body: sentences.join(" ") };
};

/** A filler cell keeps the grid's hairlines whole on a short last row. */
const fillerCount = (fieldCount: number): number => (FIELDS_PER_ROW - (fieldCount % FIELDS_PER_ROW)) % FIELDS_PER_ROW;

interface EventSavedCardProps {
  event: EventFieldsFragment;
  alertsNotSet: EventAlertNotSet[];
  onOpenEvent: (id: string) => void;
}

/** `Main`, `EventResolved`, `EventResolvedMore`, `EventAlerts`,
 * `EventAlertNotSet`, `EventAlertsPassed`, `EventAlertsCap`: the event as the
 * server understood it, with why each inferred field reads as it does. */
export const EventSavedCard = (props: EventSavedCardProps): ReactElement => {
  const { event, alertsNotSet, onOpenEvent } = props;
  const fields = savedFields(event);
  const lines = alertLines(event, alertsNotSet);
  const hasAlertsField = lines.length > 0;
  const cellCount = fields.length + (hasAlertsField ? 1 : 0);
  const notSetCopy = alertsNotSet.length > 0 ? alertsNotSetCopy(event, alertsNotSet) : null;

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillDoneStyles}`}>
          <Check size={13} /> Event saved
        </span>
      </div>
      <div className={Styles.fieldsGridStyles}>
        {fields.map((field) => (
          <div key={field.label} className={Styles.fieldCellStyles}>
            <span className={Styles.fieldLabelStyles}>{field.label}</span>
            <span className={Styles.fieldValueStyles}>{field.value}</span>
            {field.note !== null && <span className={Styles.fieldSubStyles}>{field.note}</span>}
          </div>
        ))}
        {hasAlertsField && (
          <div className={Styles.fieldCellStyles}>
            <span className={Styles.fieldLabelStyles}>{lines.length === 1 ? "Alert" : "Alerts"}</span>
            {lines.map((line) => (
              <Fragment key={line.key}>
                <span className={line.isSet ? Styles.fieldValueStyles : Styles.fieldValueDimStyles}>
                  {line.lead}
                </span>
                <span className={Styles.fieldSubStyles}>{line.note}</span>
              </Fragment>
            ))}
            {alertFieldNotes(event).map((note) => (
              <span key={note} className={Styles.fieldSubStyles}>
                {note}
              </span>
            ))}
          </div>
        )}
        {Array.from({ length: fillerCount(cellCount) }, (_, index) => (
          <div key={`filler-${index}`} className={Styles.fieldCellStyles} />
        ))}
      </div>
      {notSetCopy !== null && (
        <div className={Styles.cardNoteWrapStyles}>
          <div className={`${Styles.noteBaseStyles} ${Styles.noteWarnStyles}`}>
            <AlertCircle size={18} className="shrink-0 text-command" />
            <div className="flex-1">
              <div className={Styles.noteTitleStyles}>{notSetCopy.title}</div>
              <div className={Styles.noteBodyStyles}>{notSetCopy.body}</div>
            </div>
          </div>
        </div>
      )}
      <div className={Styles.cardFootStyles}>
        <span>Created just now · via command</span>
        <Button size="sm" onClick={() => onOpenEvent(event.id)}>
          Open in Records <ArrowRight size={14} />
        </Button>
      </div>
    </div>
  );
};

/** `EventCaptureStates` loading: 001's saving pill over the two fields every
 * event has. */
export const EventSavingCard = (): ReactElement => (
  <div className={Styles.cardStyles}>
    <div className={Styles.cardHeadStyles}>
      <span className={`${Styles.pillBaseStyles} ${Styles.pillWaitStyles}`}>
        <InlineSpinner size={11} /> Saving event
      </span>
    </div>
    <div className={Styles.eventFieldsGridStyles}>
      <div className={Styles.fieldCellStyles}>
        <span className={Styles.fieldLabelStyles}>Event</span>
        <Skeleton width="60%" height={12} />
      </div>
      <div className={Styles.fieldCellStyles}>
        <span className={Styles.fieldLabelStyles}>When</span>
        <Skeleton width="70%" height={12} />
      </div>
    </div>
  </div>
);

/** `EventsListStates` loading: skeleton date boxes and lines. */
export const EventListLoadingCard = (): ReactElement => (
  <div className={Styles.cardStyles}>
    <div className={Styles.cardHeadStyles}>
      <Skeleton width="160px" />
    </div>
    {Array.from({ length: 2 }, (_, index) => (
      <div key={index} className={Styles.eventSkeletonRowStyles}>
        <Skeleton width="46px" height={46} className="rounded-[9px]" />
        <Skeleton width="60%" height={12} />
      </div>
    ))}
  </div>
);

interface MonthGroup {
  heading: string;
  events: EventFieldsFragment[];
}

/** Consecutive events in one month, in the order given (soonest first). */
const groupByMonth = (events: EventFieldsFragment[]): MonthGroup[] => {
  const groups: MonthGroup[] = [];
  for (const event of events) {
    const heading = monthHeading(event.occurrenceDate);
    const last = groups[groups.length - 1];
    if (last !== undefined && last.heading === heading) last.events.push(event);
    else groups.push({ heading, events: [event] });
  }
  return groups;
};

interface EventListCardProps {
  events: EventFieldsFragment[];
  onOpenEvent: (id: string) => void;
  onOpenEvents: () => void;
}

/** `EventsList`: what `/events` returned, by month, soonest first (FR-24). */
export const EventListCard = (props: EventListCardProps): ReactElement => {
  const { events, onOpenEvent, onOpenEvents } = props;

  if (events.length === 0) {
    return (
      <div className={Styles.cardStyles}>
        <div className={Styles.eventEmptyStyles}>
          <CalendarDays size={20} className={Styles.eventEmptyIconStyles} />
          <div className={Styles.eventEmptyTitleStyles}>No upcoming events</div>
          <div className={Styles.eventEmptyBodyStyles}>
            Add one with <span className="font-mono">/add-event</span>, for example{" "}
            <span className="font-mono">{EVENT_EXAMPLE_COMMAND}</span>. Past events stay in Records.
          </div>
        </div>
      </div>
    );
  }

  const countLabel = `${events.length} upcoming ${events.length === 1 ? "event" : "events"}`;

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={Styles.eventListHeadStyles}>{countLabel} · soonest first</span>
      </div>
      {groupByMonth(events).map((group) => (
        <Fragment key={group.heading}>
          <div className={Styles.monthHeadStyles}>
            <span>{group.heading}</span>
            <span className={Styles.monthCountStyles}>{group.events.length}</span>
          </div>
          {group.events.map((event) => (
            <EventRow key={event.id} event={event} onOpenEvent={onOpenEvent} />
          ))}
        </Fragment>
      ))}
      <div className={Styles.cardFootStyles}>
        <span>From /events</span>
        <Button size="sm" onClick={onOpenEvents}>
          Open in Records <ArrowRight size={14} />
        </Button>
      </div>
    </div>
  );
};

interface EventRowProps {
  event: EventFieldsFragment;
  onOpenEvent: (id: string) => void;
}

/** Design §6 `.evrow`: one tab stop, Enter opens the event (design §7). */
const EventRow = (props: EventRowProps): ReactElement => {
  const { event, onOpenEvent } = props;
  const dateBox = dateBoxParts(event.occurrenceDate);
  const alerts = alertSummary(event.alerts);
  const hasMeta = event.location !== null || alerts !== null;

  return (
    <div
      role="button"
      tabIndex={0}
      className={Styles.eventRowStyles}
      onClick={() => onOpenEvent(event.id)}
      onKeyDown={(keyEvent) => {
        if (keyEvent.key === "Enter") onOpenEvent(event.id);
      }}
    >
      <div className={Styles.dateBoxStyles} aria-label={dateBox.spoken}>
        <b className={Styles.dateBoxDayStyles} aria-hidden="true">
          {dateBox.day}
        </b>
        <span className={Styles.dateBoxWeekdayStyles} aria-hidden="true">
          {dateBox.weekday}
        </span>
      </div>
      <div className="min-w-0">
        <div className={Styles.eventTitleStyles}>{event.title}</div>
        {hasMeta && (
          <div className={Styles.eventMetaStyles}>
            {event.location !== null && (
              <span className={Styles.eventMetaItemStyles}>
                <MapPin size={13} className="shrink-0" />
                {event.location}
              </span>
            )}
            {alerts !== null && (
              <span className={Styles.eventMetaAlertStyles} aria-label={alerts.spoken}>
                <Bell size={13} />
                {alerts.text}
              </span>
            )}
          </div>
        )}
      </div>
      <div className={Styles.eventWhenStyles}>{event.whenText}</div>
      <div className={Styles.eventPillsStyles}>
        {event.repeatYearly && (
          <span className={`${Styles.pillBaseStyles} ${Styles.pillRepeatStyles}`}>
            <Repeat size={12} /> Yearly
          </span>
        )}
        <EventStatusPill status={event.eventStatus} />
      </div>
    </div>
  );
};

/** `EventAsk`, FR-31: the 501st upcoming event is refused, nothing saved. */
export const EventLimitNote = (): ReactElement => (
  <div className={`${Styles.noteBaseStyles} ${Styles.noteErrStyles}`}>
    <AlertCircle size={18} className="shrink-0 text-destructive" />
    <div className="flex-1">
      <div className={Styles.noteTitleStyles}>{EVENT_LIMIT_TITLE}</div>
      <div className={Styles.noteBodyStyles}>{EVENT_LIMIT_BODY}</div>
    </div>
  </div>
);

interface EventListFailedNoteProps {
  onRetry: () => void;
}

/** `EventsListStates` error. */
export const EventListFailedNote = (props: EventListFailedNoteProps): ReactElement => {
  const { onRetry } = props;
  return (
    <div className={`${Styles.noteBaseStyles} ${Styles.noteErrStyles}`}>
      <AlertCircle size={18} className="shrink-0 text-destructive" />
      <div className="flex-1">
        <div className={Styles.noteTitleStyles}>Couldn't load your events</div>
        <div className={Styles.noteBodyStyles}>
          They are safe, and alerts still fire on time. Try again in a moment.
        </div>
        <div className={Styles.noteActionsRowStyles}>
          <Button size="sm" onClick={onRetry}>
            Try again
          </Button>
        </div>
      </div>
    </div>
  );
};
