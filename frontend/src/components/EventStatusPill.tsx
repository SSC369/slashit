import type { ReactElement } from "react";

import type { EventStatusType } from "../../types.generated";
import { EVENT_STATUS_LABEL } from "../constants/eventConstants";
import { cn } from "../utils/cn";
import * as Styles from "./styles";

const STATUS_STYLES: Record<EventStatusType, string> = {
  UPCOMING: Styles.statusPillUpcomingStyles,
  HAPPENING_NOW: Styles.statusPillHappeningStyles,
  PAST: Styles.statusPillPastStyles,
};

interface EventStatusPillProps {
  status: EventStatusType;
}

/** Upcoming, Happening now (design Q3) or Past (FR-25). */
const EventStatusPill = (props: EventStatusPillProps): ReactElement => {
  const { status } = props;
  return (
    <span className={cn(Styles.statusPillBaseStyles, STATUS_STYLES[status])}>
      {EVENT_STATUS_LABEL[status]}
    </span>
  );
};

export default EventStatusPill;
