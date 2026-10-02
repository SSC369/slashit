import { CalendarRange, Check, ChevronDown } from "lucide-react";
import type { ReactElement } from "react";

import type { ExpensePeriodFragment } from "../../../api/queries/GetExpensePeriods/responseHandler";
import Popover from "../../../design-system/components/Popover";
import { periodIdOf } from "../../../stores/ExpensesStore";
import { cn } from "../../../utils/cn";
import * as Styles from "./styles";

interface ExpensePeriodSelectProps {
  periods: ExpensePeriodFragment[];
  selected: ExpensePeriodFragment | null;
  onSelect: (periodId: string) => void;
}

/** `RecordsExpenses`' `.select` (FR-17): FR-23's periods, the named months
 * and All time, as the server resolved them. */
const ExpensePeriodSelect = (props: ExpensePeriodSelectProps): ReactElement => {
  const { periods, selected, onSelect } = props;

  return (
    <Popover
      placement="bottom-end"
      className={Styles.periodMenuStyles}
      trigger={({ isOpen, toggle }) => (
        <button
          type="button"
          className={Styles.periodSelectStyles}
          aria-haspopup="menu"
          aria-expanded={isOpen}
          aria-label={`Period, ${selected?.label ?? "loading"}`}
          disabled={periods.length === 0}
          onClick={toggle}
        >
          <CalendarRange size={14} />
          {selected?.label ?? "This month"}
          <ChevronDown size={14} />
        </button>
      )}
    >
      {({ close }) =>
        periods.map((period) => {
          const periodId = periodIdOf(period);
          const isSelected = selected !== null && periodIdOf(selected) === periodId;
          return (
            <button
              key={periodId}
              type="button"
              role="menuitemradio"
              aria-checked={isSelected}
              className={cn(Styles.periodOptionStyles, isSelected && Styles.periodOptionOnStyles)}
              onClick={() => {
                close();
                onSelect(periodId);
              }}
            >
              {period.label}
              {isSelected && <Check size={14} />}
            </button>
          );
        })
      }
    </Popover>
  );
};

export default ExpensePeriodSelect;
