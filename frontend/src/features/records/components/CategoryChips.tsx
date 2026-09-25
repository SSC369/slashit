import type { ReactElement } from "react";

import { CATEGORY_LABEL, MEMORY_CATEGORIES } from "../../../constants/memoryConstants";
import type { MemoryCategoryFilterType } from "../../../stores/MemoriesStore";
import { cn } from "../../../utils/cn";
import * as Styles from "./styles";

interface CategoryChipsProps {
  selected: MemoryCategoryFilterType;
  onSelect: (filter: MemoryCategoryFilterType) => void;
}

const CHIPS: { filter: MemoryCategoryFilterType; label: string }[] = [
  { filter: "ALL", label: "All" },
  ...MEMORY_CATEGORIES.map((category) => ({ filter: category, label: CATEGORY_LABEL[category] })),
  { filter: "UNCATEGORISED", label: "No category" },
];

/** 004 design delta `.chips`: filter within the Memories tab (FR-16). */
const CategoryChips = (props: CategoryChipsProps): ReactElement => {
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

export default CategoryChips;
