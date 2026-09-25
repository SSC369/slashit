import type { ReactElement } from "react";

import { cn } from "../utils/cn";
import * as Styles from "./styles";

interface SkeletonProps {
  width: string;
  height?: number;
  className?: string;
}

/** One grey bar standing in for text that has not loaded. Never a spinner
 * for a whole surface (design §4). */
export const Skeleton = (props: SkeletonProps): ReactElement => {
  const { width, height, className } = props;
  return (
    <span
      aria-hidden="true"
      className={cn(Styles.skeletonStyles, className)}
      style={{ width, height }}
    />
  );
};

export default Skeleton;
