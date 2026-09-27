import { Clock } from "lucide-react";
import type { ReactElement } from "react";

import * as Styles from "./styles";

interface WaitingPillProps {
  count: number;
  onShow: () => void;
}

/** 004 `Main`: "1 question waiting" above the input. Counts the questions
 * open in this session's stream (sub-plan 4.3, Q2). */
const WaitingPill = (props: WaitingPillProps): ReactElement | null => {
  const { count, onShow } = props;
  if (count === 0) return null;
  return (
    <div className={Styles.waitingPillRowStyles}>
      <button type="button" className={`${Styles.pillBaseStyles} ${Styles.pillWaitStyles}`} onClick={onShow}>
        <Clock size={13} /> {count} {count === 1 ? "question" : "questions"} waiting
      </button>
    </div>
  );
};

export default WaitingPill;
