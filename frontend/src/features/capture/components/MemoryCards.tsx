import { AlertCircle, ArrowRight, Check, Lock, Pencil, Search } from "lucide-react";
import type { ReactElement } from "react";

import CategoryTag from "../../../components/CategoryTag";
import Button from "../../../design-system/components/Button";
import {
  SECRET_CAUTION_BODY,
  SECRET_CAUTION_TITLE,
} from "../../../constants/memoryConstants";
import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import type { SecretKind } from "../../../../types.generated";
import * as Styles from "./styles";

interface MemorySavedCardProps {
  memory: MemoryFieldsFragment;
  secretCaution: SecretKind | null;
  onEditMemory: (id: string) => void;
  onOpenMemory: (id: string) => void;
}

/** `MemorySaved` and `MemorySecretCaution` (FR-7, FR-8). */
export const MemorySavedCard = (props: MemorySavedCardProps): ReactElement => {
  const { memory, secretCaution, onEditMemory, onOpenMemory } = props;

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillDoneStyles}`}>
          <Check size={13} /> Memory saved
        </span>
      </div>
      <div className={Styles.memoryFieldsGridStyles}>
        <div className={Styles.fieldCellStyles}>
          <span className={Styles.fieldLabelStyles}>Memory</span>
          <span className={Styles.fieldValueStyles}>{memory.text}</span>
        </div>
        <div className={Styles.fieldCellStyles}>
          <span className={Styles.fieldLabelStyles}>Category</span>
          <span>
            <CategoryTag category={memory.category} />
          </span>
        </div>
      </div>
      {secretCaution !== null && (
        <div role="note" className={`${Styles.noteBaseStyles} ${Styles.noteWarnStyles} ${Styles.cautionInCardStyles}`}>
          <Lock size={16} className="shrink-0 text-command" />
          <div className="text-[13px] text-foreground">
            <b>{SECRET_CAUTION_TITLE[secretCaution]}</b> {SECRET_CAUTION_BODY}
          </div>
        </div>
      )}
      <div className={Styles.cardFootStyles}>
        <span>Saved just now · via command</span>
        <div className={Styles.cardFootActionsStyles}>
          <Button size="sm" onClick={() => onEditMemory(memory.id)}>
            <Pencil size={13} /> Edit
          </Button>
          <Button size="sm" onClick={() => onOpenMemory(memory.id)}>
            Open in Records <ArrowRight size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
};

interface MemoryListCardProps {
  memories: MemoryFieldsFragment[];
  searchText: string | null;
  onOpenMemory: (id: string) => void;
  onOpenMemories: () => void;
}

/** `MemorySaved`'s list above and `MemoriesLookup` (FR-19, FR-20). */
export const MemoryListCard = (props: MemoryListCardProps): ReactElement => {
  const { memories, searchText, onOpenMemory, onOpenMemories } = props;
  const count = memories.length;
  const noun = count === 1 ? "memory" : "memories";

  if (count === 0 && searchText !== null) {
    return (
      <div className={Styles.cardStyles}>
        <div className={Styles.cardHeadStyles}>
          <span className={`${Styles.pillBaseStyles} ${Styles.pillMutedStyles}`}>
            <Search size={12} /> No memories match “{searchText}”
          </span>
        </div>
        <div className={Styles.memoryHintStyles}>
          Matching is by word. Try another word, or open Memories in Records to browse them all.
        </div>
      </div>
    );
  }

  const headLabel =
    searchText !== null
      ? `${count} ${noun} match “${searchText}”`
      : count === 0
        ? "No memories yet"
        : `${count} ${noun}`;

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillDoneStyles}`}>
          <Check size={13} /> {headLabel}
        </span>
      </div>
      {count > 0 ? (
        <div className="py-1.5">
          {memories.map((memory) => (
            <div
              key={memory.id}
              className={Styles.memoryListRowStyles}
              onClick={() => onOpenMemory(memory.id)}
            >
              <span>{memory.text}</span>
              <CategoryTag category={memory.category} />
            </div>
          ))}
        </div>
      ) : (
        <div className={Styles.memoryHintStyles}>
          Save one with /remember, for example “/remember My passport expires in 2030”.
        </div>
      )}
      <div className={Styles.cardFootStyles}>
        <span>{searchText !== null ? "Matched by word, newest first" : "Newest first"}</span>
        <Button size="sm" onClick={onOpenMemories}>
          See all in Records <ArrowRight size={14} />
        </Button>
      </div>
    </div>
  );
};

interface MemoryTooLongNoteProps {
  length: number;
  limit: number;
}

/** `CaptureStates`, FR-4: the text is back in the box to shorten. */
export const MemoryTooLongNote = (props: MemoryTooLongNoteProps): ReactElement => {
  const { length, limit } = props;
  return (
    <div className={`${Styles.noteBaseStyles} ${Styles.noteErrStyles}`}>
      <AlertCircle size={18} className="shrink-0 text-destructive" />
      <div className="text-[13.5px] text-foreground">
        <b>
          That is {length} characters. A memory can be up to {limit}.
        </b>{" "}
        Your text is still in the box, so you can shorten it. Longer writing will fit in notes when
        they arrive.
      </div>
    </div>
  );
};

interface MemoryModelDownNoteProps {
  onRetry: () => void;
}

/** `CaptureStates`, FR-9: nothing saves without the conflict check. */
export const MemoryModelDownNote = (props: MemoryModelDownNoteProps): ReactElement => {
  const { onRetry } = props;
  return (
    <div className={`${Styles.noteBaseStyles} ${Styles.noteWarnStyles}`}>
      <AlertCircle size={18} className="shrink-0 text-command" />
      <div className="flex-1 text-[13.5px] text-foreground">
        <b>Slashit could not save this right now.</b> Its AI model is unavailable, so it cannot
        check this against your other memories. This is temporary. Your text is still in the box.
        <div className={Styles.noteActionsRowStyles}>
          <Button variant="primary" size="sm" onClick={onRetry}>
            Try again
          </Button>
        </div>
      </div>
    </div>
  );
};
