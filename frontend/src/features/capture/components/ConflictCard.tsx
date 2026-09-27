import { Clock, Scale } from "lucide-react";
import { useId, useState, type ReactElement } from "react";

import BusyButton from "../../../components/BusyButton";
import Button from "../../../design-system/components/Button";
import { CATEGORY_LABEL } from "../../../constants/memoryConstants";
import type { MemoryFieldsFragment } from "../../../fragments/MemoryFields.generated";
import type { ConflictAnswer } from "../../../../types.generated";
import { formatLongDate } from "../../../utils/formatDate";
import * as Styles from "./styles";

interface ConflictCardProps {
  newText: string;
  conflicting: MemoryFieldsFragment[];
  deferred: boolean;
  error: string | null;
  isBusy: boolean;
  onAnswer: (answer: ConflictAnswer) => void;
  onDecideLater: () => void;
  onReopen: () => void;
}

const ANSWER_LABEL: Record<ConflictAnswer, string> = {
  KEEP_NEW: "Keep the new one",
  KEEP_OLD: "Keep the old one",
  BOTH: "Both are correct",
};

const ANSWERS: readonly ConflictAnswer[] = ["KEEP_NEW", "KEEP_OLD", "BOTH"];

/** FR-12: "Keep the new one" names every memory it forgets. */
const answerBody = (answer: ConflictAnswer, conflicting: MemoryFieldsFragment[]): ReactElement => {
  switch (answer) {
    case "KEEP_NEW":
      if (conflicting.length === 0) return <>Saves the new memory.</>;
      return (
        <>
          Saves the new memory and forgets{" "}
          {conflicting.map((memory, index) => (
            <span key={memory.id}>
              {index > 0 && (index === conflicting.length - 1 ? " and " : ", ")}
              <b className="text-foreground">{memory.text}</b>
            </span>
          ))}{" "}
          for good.
        </>
      );
    case "KEEP_OLD":
      return <>Discards what you just typed. Nothing new is saved.</>;
    case "BOTH":
      return (
        <>
          Saves the new memory and keeps{" "}
          {conflicting.length === 1 ? "the old one" : "the old ones"} too.
        </>
      );
  }
};

const savedMeta = (memory: MemoryFieldsFragment): string => {
  const saved = `Saved ${formatLongDate(memory.createdAt)}`;
  return memory.category === null ? saved : `${saved} · ${CATEGORY_LABEL[memory.category]}`;
};

/** 004 `Main` and `MobileConflict` (FR-10 to FR-13). Nothing is saved until an
 * answer is sent; "Decide later" folds the card and the question keeps waiting. */
export const ConflictCard = (props: ConflictCardProps): ReactElement => {
  const { newText, conflicting, deferred, error, isBusy, onAnswer, onDecideLater, onReopen } = props;
  const [selected, setSelected] = useState<ConflictAnswer>("KEEP_NEW");
  const groupName = useId();
  const noun = conflicting.length === 1 ? "a memory" : `${conflicting.length} memories`;
  const lead =
    conflicting.length === 0
      ? "The memory this contradicted has since been forgotten. Your answer still decides whether this one is saved."
      : `This contradicts ${noun} you already have.`;

  if (deferred) {
    return (
      <div className={Styles.pendingCardStyles}>
        <div className={Styles.conflictDeferredStyles}>
          <span className={`${Styles.pillBaseStyles} ${Styles.pillWaitStyles}`}>
            <Clock size={13} /> Which is correct? · Nothing saved yet
          </span>
          <Button size="sm" onClick={onReopen}>
            Answer now
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={Styles.pendingCardStyles} role="group" aria-label="Which is correct?">
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillWaitStyles}`}>
          <Scale size={13} /> Which is correct?
        </span>
        <span className="ml-auto text-xs text-foreground-tertiary">
          Nothing saved yet · answer whenever you like
        </span>
      </div>
      <div className={Styles.conflictLeadStyles}>{lead}</div>
      <div className={Styles.conflictPairStyles}>
        <div className={`${Styles.conflictSideStyles} ${Styles.conflictSideNewStyles}`} aria-label="New">
          <span className={Styles.fieldLabelStyles}>New</span>
          <div className={Styles.conflictSideTextStyles}>{newText}</div>
          <div className={Styles.conflictSideMetaStyles}>Just now</div>
        </div>
        {conflicting.map((memory) => (
          <div key={memory.id} className={Styles.conflictSideStyles} aria-label="Saved before">
            <span className={Styles.fieldLabelStyles}>You saved before</span>
            <div className={Styles.conflictSideTextStyles}>{memory.text}</div>
            <div className={Styles.conflictSideMetaStyles}>{savedMeta(memory)}</div>
          </div>
        ))}
      </div>
      <div role="radiogroup" aria-label="Which is correct?" className="border-t border-border">
        {ANSWERS.map((answer) => (
          <label
            key={answer}
            className={`${Styles.conflictAnswerRowStyles} ${selected === answer ? Styles.conflictAnswerRowOnStyles : ""}`}
          >
            <input
              type="radio"
              name={groupName}
              className={`${Styles.forgetRadioStyles} mt-0.5`}
              aria-label={ANSWER_LABEL[answer]}
              checked={selected === answer}
              autoFocus={answer === "KEEP_NEW"}
              disabled={isBusy}
              onChange={() => setSelected(answer)}
              onKeyDown={(event) => {
                if (event.key !== "Enter") return;
                event.preventDefault();
                onAnswer(selected);
              }}
            />
            <span>
              <span className={Styles.conflictAnswerTitleStyles}>{ANSWER_LABEL[answer]}</span>
              <span className={`block ${Styles.conflictAnswerBodyStyles}`}>
                {answerBody(answer, conflicting)}
              </span>
            </span>
          </label>
        ))}
      </div>
      {error !== null && (
        <div className={Styles.forgetErrorStyles} role="alert">
          {error} Nothing changed.
        </div>
      )}
      <div className={Styles.conflictActionsStyles}>
        <Button disabled={isBusy} onClick={onDecideLater}>
          Decide later
        </Button>
        <BusyButton variant="primary" isBusy={isBusy} busyLabel="Saving your answer" onClick={() => onAnswer(selected)}>
          {error !== null ? "Try again" : ANSWER_LABEL[selected]}
        </BusyButton>
      </div>
    </div>
  );
};

interface ConflictOutcomeProps {
  kind: "discarded" | "gone";
}

/** The answer's outcome when nothing new was saved. */
export const ConflictOutcomeNote = (props: ConflictOutcomeProps): ReactElement => {
  const { kind } = props;
  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillMutedStyles}`}>
          {kind === "discarded" ? "Kept your earlier memory" : "Already answered"}
        </span>
      </div>
      <div className={Styles.memoryHintStyles}>
        {kind === "discarded"
          ? "Nothing new was saved."
          : "This question was answered in another tab. Nothing changed here."}
      </div>
    </div>
  );
};
