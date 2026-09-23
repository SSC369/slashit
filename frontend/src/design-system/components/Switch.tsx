import type { ReactElement } from "react";

import { cn } from "../../utils/cn";

interface SwitchProps {
  isOn: boolean;
  /** Names the setting for screen readers: "Email". */
  label: string;
  isBusy?: boolean;
  onToggle: (isOn: boolean) => void;
}

/**
 * A two-state control (design §6 delta, "Switch"). While its change saves it
 * is dimmed and disabled, so a second press cannot race the first.
 */
const Switch = (props: SwitchProps): ReactElement => {
  const { isOn, label, isBusy = false, onToggle } = props;
  return (
    <button
      type="button"
      role="switch"
      aria-checked={isOn}
      aria-label={label}
      aria-busy={isBusy}
      disabled={isBusy}
      onClick={() => onToggle(!isOn)}
      className={cn(
        "relative h-[23px] w-10 shrink-0 rounded-full transition-colors motion-reduce:transition-none disabled:cursor-not-allowed disabled:opacity-60",
        isOn ? "bg-accent" : "bg-border-strong",
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "absolute top-[2.5px] left-[2.5px] h-[18px] w-[18px] rounded-full bg-white shadow-sm transition-transform motion-reduce:transition-none",
          isOn && "translate-x-[17px]",
        )}
      />
    </button>
  );
};

export default Switch;
