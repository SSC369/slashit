import type { ReactElement } from "react";

import { CATEGORY_LABEL } from "../constants/memoryConstants";
import type { MemoryCategory } from "../../types.generated";
import { cn } from "../utils/cn";
import * as Styles from "./styles";

interface CategoryTagProps {
  category: MemoryCategory | null;
}

/** 004 design delta `.cat`: neutral, because a category is not a state;
 * dashed when a memory has none (FR-6). */
export const CategoryTag = (props: CategoryTagProps): ReactElement => {
  const { category } = props;
  if (category === null) {
    return <span className={cn(Styles.categoryTagStyles, Styles.categoryTagNoneStyles)}>No category</span>;
  }
  return <span className={Styles.categoryTagStyles}>{CATEGORY_LABEL[category]}</span>;
};

export default CategoryTag;
