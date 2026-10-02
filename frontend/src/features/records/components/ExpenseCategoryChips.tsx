import type { ReactElement } from "react";

import { EXPENSE_CATEGORIES, EXPENSE_CATEGORY_LABEL } from "../../../constants/expenseConstants";
import type { ExpenseCategoryFilterType } from "../../../stores/ExpensesStore";
import { cn } from "../../../utils/cn";
import * as Styles from "./styles";

interface ExpenseCategoryChipsProps {
  selected: ExpenseCategoryFilterType;
  onSelect: (filter: ExpenseCategoryFilterType) => void;
}

const CHIPS: { filter: ExpenseCategoryFilterType; label: string }[] = [
  { filter: "ALL", label: "All" },
  ...EXPENSE_CATEGORIES.map((category) => ({ filter: category, label: EXPENSE_CATEGORY_LABEL[category] })),
];

/** 004's `.chips`, with FR-9's eight: filter within the Expenses tab (FR-17). */
const ExpenseCategoryChips = (props: ExpenseCategoryChipsProps): ReactElement => {
  const { selected, onSelect } = props;
  return (
    <div className={Styles.categoryChipsRowStyles} role="group" aria-label="Filter by category">
      {CHIPS.map((chip) => (
        <button
          key={chip.filter}
          type="button"
          aria-pressed={selected === chip.filter}
          className={cn(Styles.categoryChipStyles, selected === chip.filter && Styles.categoryChipOnStyles)}
          onClick={() => onSelect(chip.filter)}
        >
          {chip.label}
        </button>
      ))}
    </div>
  );
};

export default ExpenseCategoryChips;
