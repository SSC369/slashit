import { Clock } from "lucide-react";
import type { ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import Popover from "../../../design-system/components/Popover";
import { buildSnoozeChoices, type SnoozeOptionType } from "../../../utils/formatNotification";
import * as Styles from "./styles";

interface SnoozeMenuProps {
  defaultReminderTime: string | null;
  isBusy: boolean;
  isDisabled: boolean;
  placement: "top-start" | "bottom-start";
  onPick: (option: SnoozeOptionType) => void;
}

/** FR-21: three choices, each showing the time it lands on. */
const SnoozeMenu = (props: SnoozeMenuProps): ReactElement => {
  const { defaultReminderTime, isBusy, isDisabled, placement, onPick } = props;

  return (
    <Popover
      placement={placement}
      trigger={({ isOpen, toggle }) => (
        <BusyButton
          size="sm"
          isBusy={isBusy}
          busyLabel="Snoozing"
          disabled={isDisabled}
          aria-haspopup="menu"
          aria-expanded={isOpen}
          onClick={toggle}
        >
          <Clock size={13} /> Snooze
        </BusyButton>
      )}
    >
      {({ close }) =>
        buildSnoozeChoices(new Date(), defaultReminderTime).map((choice) => (
          <button
            key={choice.option}
            type="button"
            role="menuitem"
            aria-label={
              choice.resultingTime ? `${choice.label}, ${choice.resultingTime}` : choice.label
            }
            className={Styles.snoozeOptionStyles}
            onClick={() => {
              close();
              onPick(choice.option);
            }}
          >
            <span>{choice.label}</span>
            <span className={Styles.snoozeTimeStyles}>{choice.resultingTime}</span>
          </button>
        ))
      }
    </Popover>
  );
};

export default SnoozeMenu;
