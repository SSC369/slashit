import type { ReactElement } from "react";

import * as Styles from "./styles";

interface ShareBarProps {
  /** 0 to 1: this amount's share of the largest in the same list. */
  share: number;
}

/** Design §7: decorative, beside its amount in text, so hidden from screen
 * readers. */
const ShareBar = (props: ShareBarProps): ReactElement => {
  const { share } = props;
  return (
    <div className={Styles.shareBarTrackStyles} aria-hidden="true">
      <i className={Styles.shareBarFillStyles} style={{ width: `${Math.max(0, Math.min(share, 1)) * 100}%` }} />
    </div>
  );
};

export default ShareBar;
