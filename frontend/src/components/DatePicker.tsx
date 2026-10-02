import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent, type ReactElement } from "react";

import Button from "../design-system/components/Button";
import { cn } from "../utils/cn";
import {
  addDays,
  addMonths,
  dayOfMonth,
  formatDayLong,
  formatMonthYear,
  isSameMonth,
  monthGrid,
} from "../utils/localDate";
import * as Styles from "./styles";

const WEEKDAY_HEADINGS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

/** Design §7: arrows move by day, Page Up and Page Down by month. */
const KEY_MOVES: Record<string, (iso: string) => string> = {
  ArrowLeft: (iso) => addDays(iso, -1),
  ArrowRight: (iso) => addDays(iso, 1),
  ArrowUp: (iso) => addDays(iso, -7),
  ArrowDown: (iso) => addDays(iso, 7),
  PageUp: (iso) => addMonths(iso, -1),
  PageDown: (iso) => addMonths(iso, 1),
};

interface DatePickerProps {
  /** The chosen day, ISO. The calendar opens on its month. */
  value: string;
  /** The user's today, ISO; ringed. */
  today: string;
  onChange: (iso: string) => void;
  /** Take focus on the chosen day when opened. */
  autoFocus?: boolean;
}

/**
 * `DatePick`'s calendar (006 design §6), shared by capture's date question and
 * the edit form. Any date can be chosen, past or future (FR-8, FR-21).
 */
const DatePicker = (props: DatePickerProps): ReactElement => {
  const { value, today, onChange, autoFocus = false } = props;
  // The day the keyboard is on; the grid shows its month.
  const [focusedDay, setFocusedDay] = useState(value);
  const [shouldFocus, setShouldFocus] = useState(autoFocus);
  const gridRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!shouldFocus) return;
    gridRef.current?.querySelector<HTMLButtonElement>(`[data-day="${focusedDay}"]`)?.focus();
  }, [focusedDay, shouldFocus]);

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>): void => {
    const move = KEY_MOVES[event.key];
    if (move === undefined) return;
    event.preventDefault();
    setShouldFocus(true);
    setFocusedDay(move(focusedDay));
  };

  const choose = (iso: string): void => {
    setFocusedDay(iso);
    onChange(iso);
  };

  return (
    <div className={Styles.calendarStyles}>
      <div className={Styles.calendarHeadStyles}>
        <Button
          size="sm"
          className={Styles.calendarNavButtonStyles}
          aria-label="Previous month"
          onClick={() => setFocusedDay(addMonths(focusedDay, -1))}
        >
          <ChevronLeft size={14} />
        </Button>
        <span className={Styles.calendarMonthStyles} aria-live="polite">
          {formatMonthYear(focusedDay)}
        </span>
        <Button
          size="sm"
          className={Styles.calendarNavButtonStyles}
          aria-label="Next month"
          onClick={() => setFocusedDay(addMonths(focusedDay, 1))}
        >
          <ChevronRight size={14} />
        </Button>
      </div>
      <div ref={gridRef} role="grid" aria-label={formatMonthYear(focusedDay)} onKeyDown={handleKeyDown}>
        <div role="row" className={Styles.calendarGridStyles}>
          {WEEKDAY_HEADINGS.map((weekday) => (
            <span key={weekday} role="columnheader" className={Styles.calendarWeekdayStyles}>
              {weekday}
            </span>
          ))}
        </div>
        {monthGrid(focusedDay).map((week) => (
          <div key={week[0]} role="row" className={Styles.calendarGridStyles}>
            {week.map((day) => (
              <button
                key={day}
                type="button"
                role="gridcell"
                data-day={day}
                aria-label={formatDayLong(day)}
                aria-selected={day === value}
                aria-current={day === today ? "date" : undefined}
                tabIndex={day === focusedDay ? 0 : -1}
                className={cn(
                  Styles.calendarDayStyles,
                  !isSameMonth(day, focusedDay) && Styles.calendarDayOutsideStyles,
                  day === today && Styles.calendarDayTodayStyles,
                  day === value && Styles.calendarDaySelectedStyles,
                )}
                onClick={() => choose(day)}
              >
                {dayOfMonth(day)}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default DatePicker;
