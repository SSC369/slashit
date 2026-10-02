import type { ReactElement } from "react";

import * as Styles from "./styles";

/** Design §6 `.dot.evt`: a green diamond. Square is task, round is reminder
 * and memory. Read as "Event" (design §7). */
const EventMarker = (): ReactElement => <span role="img" aria-label="Event" className={Styles.eventMarkerStyles} />;

export default EventMarker;
