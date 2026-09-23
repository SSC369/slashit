import type { ReactElement } from "react";

import Button, { type ButtonProps } from "../design-system/components/Button";
import { cn } from "../utils/cn";
import * as Styles from "./styles";

interface BusyButtonProps extends ButtonProps {
  isBusy: boolean;
  /** Read by screen readers while the visible label is hidden: "Saving". */
  busyLabel: string;
}

/**
 * A button whose label a spinner replaces while its action runs (design §6,
 * "Button busy state"). The label stays in the layout, invisible, so the
 * button keeps its width. Busy also disables it, so a second press cannot
 * send the action twice.
 */
export const BusyButton = (props: BusyButtonProps): ReactElement => {
  const { isBusy, busyLabel, children, className, disabled, ...rest } = props;
  return (
    <Button
      {...rest}
      className={cn(Styles.busyButtonStyles, className)}
      disabled={disabled === true || isBusy}
      aria-busy={isBusy}
      aria-label={isBusy ? busyLabel : rest["aria-label"]}
    >
      <span className={cn(Styles.busyButtonLabelStyles, isBusy && "invisible")}>{children}</span>
      {isBusy && (
        <span className={Styles.busyButtonSpinnerWrapStyles}>
          <span className={Styles.busyButtonSpinnerStyles} data-testid="busy-spinner" />
        </span>
      )}
    </Button>
  );
};

export default BusyButton;
