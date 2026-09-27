import type { ReactElement } from "react";

import CategoryTag from "../../../components/CategoryTag";
import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import { cn } from "../../../utils/cn";
import { formatShortDate } from "../../../utils/formatDate";
import * as Styles from "./styles";

interface MemoryTableProps {
  memories: MemoryFieldsFragment[];
  isLoading: boolean;
  onOpenMemory: (id: string) => void;
}

const SKELETON_ROW_COUNT = 3;

/** 004 `RecordsMemories` (FR-15): text, category, saved date, newest first. */
const MemoryTable = (props: MemoryTableProps): ReactElement => {
  const { memories, isLoading, onOpenMemory } = props;
  const count = memories.length;

  return (
    <div className={Styles.cardStyles}>
      <table className={Styles.tableStyles}>
        <thead>
          <tr className={Styles.theadRowStyles}>
            <th className={Styles.thStyles}>Memory</th>
            <th className={Styles.thStyles} style={{ width: 170 }}>
              Category
            </th>
            <th className={Styles.thStyles} style={{ width: 160 }}>
              Saved
            </th>
          </tr>
        </thead>
        <tbody>
          {isLoading
            ? Array.from({ length: SKELETON_ROW_COUNT }, (_, index) => (
                <tr key={index} className={Styles.rowStyles} aria-hidden="true">
                  <td className={Styles.tdStyles}>
                    <div className={Styles.skeletonBlockStyles} style={{ width: "55%" }} />
                  </td>
                  <td className={Styles.tdStyles}>
                    <div className={Styles.skeletonBlockStyles} style={{ width: "50%" }} />
                  </td>
                  <td className={Styles.tdStyles}>
                    <div className={Styles.skeletonBlockStyles} style={{ width: "45%" }} />
                  </td>
                </tr>
              ))
            : memories.map((memory) => (
                <tr
                  key={memory.id}
                  className={Styles.rowStyles}
                  onClick={() => onOpenMemory(memory.id)}
                >
                  <td className={cn(Styles.tdStyles, Styles.memoryTextCellStyles)}>{memory.text}</td>
                  <td className={Styles.tdStyles}>
                    <CategoryTag category={memory.category} />
                  </td>
                  <td className={cn(Styles.tdStyles, Styles.dateCellStyles)}>
                    {formatShortDate(memory.createdAt)}
                  </td>
                </tr>
              ))}
        </tbody>
      </table>
      {!isLoading && (
        <div className={Styles.cardFootStyles}>
          <span>
            {count} {count === 1 ? "memory" : "memories"}
          </span>
          <span>Only you can see these</span>
        </div>
      )}
    </div>
  );
};

export default MemoryTable;
