import { Check, Eraser, Search } from "lucide-react";
import { useId, type ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import CategoryTag from "../../../components/CategoryTag";
import Button from "../../../design-system/components/Button";
import { BACKUP_LINE, FORGET_PICK_LIMIT } from "../../../constants/memoryConstants";
import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import * as Styles from "./styles";

const memoriesNoun = (count: number): string => (count === 1 ? "memory" : "memories");

interface ForgetPickCardProps {
  candidates: MemoryFieldsFragment[];
  totalMatches: number;
  selectedId: string | null;
  onSelect: (memoryId: string) => void;
  onContinue: () => void;
  onCancel: () => void;
}

/** `ForgetPick`, FR-25: one radio group, so arrow keys move and nothing goes until Continue. */
export const ForgetPickCard = (props: ForgetPickCardProps): ReactElement => {
  const { candidates, totalMatches, selectedId, onSelect, onContinue, onCancel } = props;
  const moreCount = totalMatches - candidates.length;
  const groupName = useId();

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillMutedStyles}`}>
          <Search size={12} /> Several memories match
        </span>
        <span className="ml-auto text-xs text-foreground-tertiary">Pick one to forget</span>
      </div>
      <div role="radiogroup" aria-label="Pick one to forget">
        {candidates.map((memory) => {
          const isSelected = memory.id === selectedId;
          return (
            <label
              key={memory.id}
              className={`${Styles.forgetPickRowStyles} ${isSelected ? Styles.forgetPickRowOnStyles : ""}`}
            >
              <input
                type="radio"
                name={groupName}
                aria-label={memory.text}
                className={Styles.forgetRadioStyles}
                checked={isSelected}
                onChange={() => onSelect(memory.id)}
              />
              <span className="flex-1">{memory.text}</span>
              <CategoryTag category={memory.category} />
            </label>
          );
        })}
      </div>
      {moreCount > 0 && (
        <div className={Styles.memoryHintStyles}>
          {moreCount} more match. Showing the {FORGET_PICK_LIMIT} closest; use more words, or forget from
          Records.
        </div>
      )}
      <div className={Styles.forgetActionsStyles}>
        <Button onClick={onCancel}>Cancel</Button>
        <Button variant="primary" disabled={selectedId === null} onClick={onContinue}>
          Continue
        </Button>
      </div>
    </div>
  );
};

interface ForgetConfirmCardProps {
  memory: MemoryFieldsFragment;
  error: string | null;
  isBusy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/** `ForgetConfirm`, FR-24 and FR-29: names the full text. Focus starts on Cancel. */
export const ForgetConfirmCard = (props: ForgetConfirmCardProps): ReactElement => {
  const { memory, error, isBusy, onConfirm, onCancel } = props;

  return (
    <div className={Styles.forgetConfirmCardStyles} role="group" aria-label="Forget this memory?">
      <div className={Styles.forgetConfirmBodyStyles}>
        <div className={Styles.forgetConfirmIconStyles}>
          <Eraser size={17} />
        </div>
        <div>
          <div className={Styles.forgetConfirmTitleStyles}>Forget this memory?</div>
          <div className={Styles.forgetConfirmTextStyles}>
            <b className="text-foreground">{memory.text}</b> will be removed for good. Its words are
            also removed from your capture history. This cannot be undone.
          </div>
          <div className={Styles.forgetConfirmBackupStyles}>{BACKUP_LINE}</div>
        </div>
      </div>
      {error !== null && (
        <div className={Styles.forgetErrorStyles} role="alert">
          {error} Nothing was forgotten.
        </div>
      )}
      <div className={Styles.forgetActionsStyles}>
        <Button autoFocus disabled={isBusy} onClick={onCancel}>
          Cancel
        </Button>
        <BusyButton variant="danger" isBusy={isBusy} busyLabel="Forgetting" onClick={onConfirm}>
          {error !== null ? "Try again" : "Forget memory"}
        </BusyButton>
      </div>
    </div>
  );
};

interface ForgetAllCardProps {
  count: number;
  countChanged: boolean;
  error: string | null;
  isBusy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/** `ForgetAll`, FR-27: the count is in the title and the button. */
export const ForgetAllCard = (props: ForgetAllCardProps): ReactElement => {
  const { count, countChanged, error, isBusy, onConfirm, onCancel } = props;

  if (count === 0) {
    return (
      <div className={Styles.cardStyles}>
        <div className={Styles.cardHeadStyles}>
          <span className={`${Styles.pillBaseStyles} ${Styles.pillMutedStyles}`}>No memories</span>
        </div>
        <div className={Styles.memoryHintStyles}>You have no memories to forget. Nothing was changed.</div>
      </div>
    );
  }

  const noun = memoriesNoun(count);
  const title = `Forget all ${count} ${noun}?`;

  return (
    <div className={Styles.forgetConfirmCardStyles} role="group" aria-label={title}>
      <div className={Styles.forgetConfirmBodyStyles}>
        <div className={Styles.forgetConfirmIconStyles}>
          <Eraser size={17} />
        </div>
        <div>
          <div className={Styles.forgetConfirmTitleStyles}>{title}</div>
          {countChanged && (
            <div className={`${Styles.forgetConfirmTextStyles} font-semibold text-foreground`} role="status">
              Your memories changed since you asked. You now have {count}.
            </div>
          )}
          <div className={Styles.forgetConfirmTextStyles}>
            Every memory you have saved will be removed for good, and their words removed from your
            capture history. This cannot be undone.
          </div>
          <div className={Styles.forgetConfirmBackupStyles}>{BACKUP_LINE}</div>
        </div>
      </div>
      {error !== null && (
        <div className={Styles.forgetErrorStyles} role="alert">
          {error} Nothing was forgotten.
        </div>
      )}
      <div className={Styles.forgetActionsStyles}>
        <Button autoFocus disabled={isBusy} onClick={onCancel}>
          Cancel
        </Button>
        <BusyButton variant="danger" isBusy={isBusy} busyLabel="Forgetting" onClick={onConfirm}>
          {error !== null ? "Try again" : `Forget ${count} ${noun}`}
        </BusyButton>
      </div>
    </div>
  );
};

interface ForgetNoMatchNoteProps {
  searchText: string;
}

/** `CaptureStates`, FR-26. A bare `/forget` says how to use it (user, 2026-09-25). */
export const ForgetNoMatchNote = (props: ForgetNoMatchNoteProps): ReactElement => {
  const { searchText } = props;

  if (searchText === "") {
    return (
      <div className={Styles.cardStyles}>
        <div className={Styles.cardHeadStyles}>
          <span className={`${Styles.pillBaseStyles} ${Styles.pillMutedStyles}`}>Nothing forgotten</span>
        </div>
        <div className={Styles.memoryHintStyles}>
          Type what to forget, for example “/forget airline”, or “/forget all”.
        </div>
      </div>
    );
  }

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillMutedStyles}`}>
          <Search size={12} /> No memory matches “{searchText}”
        </span>
      </div>
      <div className={Styles.memoryHintStyles}>
        No memory matches “{searchText}”. Nothing was forgotten.
      </div>
    </div>
  );
};

interface ForgottenNoteProps {
  count: number;
}

/** Success: what the history row will also say (FR-28). */
export const ForgottenNote = (props: ForgottenNoteProps): ReactElement => {
  const { count } = props;
  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillDoneStyles}`}>
          <Check size={13} /> Forgot {count} {memoriesNoun(count)}
        </span>
      </div>
      <div className={Styles.memoryHintStyles}>
        {count === 1 ? "Memory forgotten." : "Memories forgotten."} Gone from your records and your
        capture history.
      </div>
    </div>
  );
};

/** The picked memory was forgotten elsewhere before this confirm (sub-plan 4.2 §6). */
export const ForgetGoneNote = (): ReactElement => (
  <div className={Styles.cardStyles}>
    <div className={Styles.cardHeadStyles}>
      <span className={`${Styles.pillBaseStyles} ${Styles.pillMutedStyles}`}>Already gone</span>
    </div>
    <div className={Styles.memoryHintStyles}>That memory is already forgotten. Nothing else changed.</div>
  </div>
);

export const ForgetCancelledNote = (): ReactElement => (
  <div className={Styles.cardStyles}>
    <div className={Styles.cardHeadStyles}>
      <span className={`${Styles.pillBaseStyles} ${Styles.pillMutedStyles}`}>Cancelled</span>
    </div>
    <div className={Styles.memoryHintStyles}>Nothing was forgotten.</div>
  </div>
);
