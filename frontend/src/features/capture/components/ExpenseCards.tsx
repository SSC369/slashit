import {
  ArrowRight,
  Calendar,
  Check,
  CircleQuestionMark,
  CircleX,
  Clock,
  Pencil,
  TriangleAlert,
} from "lucide-react";
import { useState, type ReactElement, type ReactNode } from "react";

import ExpenseCategoryTag from "../../../components/ExpenseCategoryTag";
import DatePicker from "../../../components/DatePicker";
import InlineSpinner from "../../../components/InlineSpinner";
import Skeleton from "../../../components/Skeleton";
import Button from "../../../design-system/components/Button";
import { MAX_DESCRIPTION_LENGTH, type ExpenseQuestionArgs } from "../../../constants/expenseConstants";
import type { ExpenseFieldsFragment } from "../../../fragments/ExpenseFields.generated";
import type { ExpenseRefusalReason } from "../../../../types.generated";
import { cn } from "../../../utils/cn";
import { formatDayLong, formatDayShort, formatSpentOn, todayIso } from "../../../utils/localDate";
import { formatRupees, spokenRupees } from "../../../utils/money";
import * as Styles from "./styles";

/** `CaptureMoreStates`, loading · saving. */
export const ExpenseLoadingCard = (): ReactElement => (
  <div className={Styles.cardStyles}>
    <div className={Styles.cardHeadStyles}>
      <span className={`${Styles.pillBaseStyles} ${Styles.pillWaitStyles}`}>
        <Clock size={13} /> Reading your expense…
      </span>
    </div>
    <div className={Styles.expenseLoadingBodyStyles}>
      <Skeleton width="60%" />
      <Skeleton width="40%" />
    </div>
  </div>
);

/** An amount in mono, read aloud as rupees (design §7). */
export const Amount = (props: { paise: string; className?: string }): ReactElement => {
  const { paise, className } = props;
  return (
    <span className={cn(Styles.amountStyles, className)} aria-label={spokenRupees(paise)}>
      {formatRupees(paise)}
    </span>
  );
};

interface ExpenseSavedCardProps {
  expense: ExpenseFieldsFragment;
  onEditExpense: (id: string) => void;
  onOpenExpense: (id: string) => void;
}

/** `Main`, FR-12: the four fields read back where they were typed. */
export const ExpenseSavedCard = (props: ExpenseSavedCardProps): ReactElement => {
  const { expense, onEditExpense, onOpenExpense } = props;

  return (
    <div className={Styles.cardStyles}>
      <div className={Styles.cardHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillDoneStyles}`}>
          <Check size={13} /> Expense saved
        </span>
      </div>
      <div className={Styles.expenseFieldsGridStyles}>
        <div className={Styles.fieldCellStyles}>
          <span className={Styles.fieldLabelStyles}>Amount</span>
          <Amount paise={expense.amountPaise} className={Styles.expenseAmountValueStyles} />
        </div>
        <div className={Styles.fieldCellStyles}>
          <span className={Styles.fieldLabelStyles}>Description</span>
          <span className={Styles.fieldValueStyles}>{expense.description}</span>
        </div>
        <div className={Styles.fieldCellStyles}>
          <span className={Styles.fieldLabelStyles}>Category</span>
          <span>
            <ExpenseCategoryTag category={expense.category} />
          </span>
        </div>
        <div className={Styles.fieldCellStyles}>
          <span className={Styles.fieldLabelStyles}>Date</span>
          <span className={Styles.fieldValueStyles}>{formatSpentOn(expense.spentOn, todayIso())}</span>
        </div>
      </div>
      <div className={Styles.cardFootStyles}>
        <span>Saved just now · via command</span>
        <div className={Styles.cardFootActionsStyles}>
          <Button size="sm" onClick={() => onEditExpense(expense.id)}>
            <Pencil size={13} /> Edit
          </Button>
          <Button size="sm" onClick={() => onOpenExpense(expense.id)}>
            Open in Records <ArrowRight size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
};

interface ExpenseRefusedNoteProps {
  reason: ExpenseRefusalReason;
  length: number | null;
}

/** `CaptureStates`, FR-6 and FR-13: refused, the text back in the box. */
export const ExpenseRefusedNote = (props: ExpenseRefusedNoteProps): ReactElement => {
  const { reason, length } = props;
  return (
    <div role="alert" className={`${Styles.noteBaseStyles} ${Styles.noteErrStyles}`}>
      <CircleX size={18} className="shrink-0 text-destructive" />
      <div className={Styles.expenseNoteTextStyles}>
        {reason === "FOREIGN_CURRENCY" ? (
          <>
            <b>Slashit records rupees only for now.</b> Enter the amount in ₹ and it will save. Your
            text is still in the box.
          </>
        ) : (
          <>
            <b>
              That description is {length ?? "over " + MAX_DESCRIPTION_LENGTH} characters. It can be up
              to {MAX_DESCRIPTION_LENGTH}.
            </b>{" "}
            Your text is still in the box, so you can shorten it.
          </>
        )}
      </div>
    </div>
  );
};

/** `CaptureStates`, FR-14: nothing saved, the text back in the box. */
export const ExpenseModelDownNote = (): ReactElement => (
  <div role="alert" className={`${Styles.noteBaseStyles} ${Styles.noteWarnStyles}`}>
    <TriangleAlert size={18} className="shrink-0 text-command" />
    <div className={Styles.expenseNoteTextStyles}>
      <b>Slashit could not save this right now.</b> Its AI model is unavailable. This is temporary.
      Your text is still in the box.
    </div>
  </div>
);

const COUNT_WORDS = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];

const QUESTION_HINT: Record<ExpenseQuestionArgs["kind"], (candidateCount: number) => string> = {
  AMOUNT: () => "Reply with the amount in rupees. Nothing is saved until you answer.",
  DESCRIPTION: () => "Reply with a few words. Nothing is saved until you answer.",
  AMOUNT_CHOICE: (count) =>
    `Your text has ${COUNT_WORDS[count] ?? count} numbers. Nothing is saved until you pick one.`,
  DATE: () => "Confirm the date Slashit read, or pick another. Nothing is saved until you choose.",
};

const ANSWER_PLACEHOLDER: Record<"AMOUNT" | "DESCRIPTION", string> = {
  AMOUNT: "₹ amount…",
  DESCRIPTION: "What it was for…",
};

/** `ExpenseAsk` bolds the date inside the server's sentence. */
const withDateBold = (question: string, readDate: string | null): ReactNode => {
  if (readDate === null) return question;
  const dateText = formatDayShort(readDate);
  const at = question.indexOf(dateText);
  if (at === -1) return question;
  return (
    <>
      {question.slice(0, at)}
      <b>{dateText}</b>
      {question.slice(at + dateText.length)}
    </>
  );
};

interface ExpenseQuestionCardProps extends ExpenseQuestionArgs {
  answerDraft: string;
  isAnswering: boolean;
  onAnswerDraftChange: (draft: string) => void;
  onAnswerSubmit: () => void;
  /** A chip, "Yes, {date}" or the calendar: the answer is sent as it is. */
  onAnswer: (answer: string) => void;
  onDiscard: () => void;
}

/** `ExpenseAsk`, `AmountPick` and `DatePick` (FR-3 to FR-5, FR-8). */
export const ExpenseQuestionCard = (props: ExpenseQuestionCardProps): ReactElement => {
  const { kind, question, amountCandidates, readDate, isAnswering } = props;

  return (
    <div className={Styles.pendingCardStyles}>
      <div className={Styles.pendingHeadStyles}>
        <span className={`${Styles.pillBaseStyles} ${Styles.pillWaitStyles}`}>
          <CircleQuestionMark size={13} /> One question
        </span>
        {isAnswering && <InlineSpinner className="ml-auto" />}
      </div>
      <div className={Styles.pendingBodyStyles}>
        <div className={Styles.pendingQuestionStyles}>{withDateBold(question, readDate)}</div>
        <div className={Styles.pendingHintStyles}>{QUESTION_HINT[kind](amountCandidates.length)}</div>
        <QuestionAnswer {...props} />
      </div>
    </div>
  );
};

const QuestionAnswer = (props: ExpenseQuestionCardProps): ReactElement => {
  const {
    kind,
    amountCandidates,
    readDate,
    answerDraft,
    isAnswering,
    onAnswerDraftChange,
    onAnswerSubmit,
    onAnswer,
    onDiscard,
  } = props;

  switch (kind) {
    case "AMOUNT_CHOICE":
      return (
        <div className={Styles.choiceChipsRowStyles}>
          {amountCandidates.map((paise, index) => (
            <button
              key={paise}
              type="button"
              autoFocus={index === 0}
              disabled={isAnswering}
              className={cn(
                Styles.choiceChipStyles,
                isAnswering && answerDraft === paise && Styles.choiceChipOnStyles,
              )}
              aria-label={spokenRupees(paise)}
              onClick={() => onAnswer(paise)}
            >
              {formatRupees(paise)}
            </button>
          ))}
          <Button className="ml-auto" disabled={isAnswering} onClick={onDiscard}>
            Discard
          </Button>
        </div>
      );
    case "DATE":
      return (
        <DateAnswer readDate={readDate ?? todayIso()} isAnswering={isAnswering} onAnswer={onAnswer} onDiscard={onDiscard} />
      );
    case "AMOUNT":
    case "DESCRIPTION":
      return (
        <div className={Styles.pendingAnswerRowStyles}>
          <div className={Styles.pendingAnswerFieldStyles}>
            <input
              className={Styles.pendingAnswerInputStyles}
              type="text"
              autoFocus
              inputMode={kind === "AMOUNT" ? "decimal" : undefined}
              aria-label={kind === "AMOUNT" ? "Amount in rupees" : "What the expense was for"}
              placeholder={ANSWER_PLACEHOLDER[kind]}
              value={answerDraft}
              disabled={isAnswering}
              onChange={(event) => onAnswerDraftChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key !== "Enter") return;
                event.preventDefault();
                onAnswerSubmit();
              }}
            />
          </div>
          <Button onClick={onDiscard} disabled={isAnswering}>
            Discard
          </Button>
        </div>
      );
  }
};

interface DateAnswerProps {
  readDate: string;
  isAnswering: boolean;
  onAnswer: (answer: string) => void;
  onDiscard: () => void;
}

/** FR-8: "Yes, {date}", or a calendar to choose another. */
const DateAnswer = (props: DateAnswerProps): ReactElement => {
  const { readDate, isAnswering, onAnswer, onDiscard } = props;
  const [isPicking, setIsPicking] = useState(false);
  const [chosenDate, setChosenDate] = useState(readDate);

  if (!isPicking) {
    return (
      <div className={Styles.expenseQuestionActionsStyles}>
        <Button variant="primary" size="sm" autoFocus disabled={isAnswering} onClick={() => onAnswer(readDate)}>
          <Check size={13} /> Yes, {formatDayShort(readDate)}
        </Button>
        <Button size="sm" disabled={isAnswering} onClick={() => setIsPicking(true)}>
          <Calendar size={14} /> Pick another date
        </Button>
        <Button size="sm" disabled={isAnswering} onClick={onDiscard}>
          Discard
        </Button>
      </div>
    );
  }

  return (
    <div className={Styles.datePickRowStyles}>
      <DatePicker value={chosenDate} today={todayIso()} onChange={setChosenDate} autoFocus />
      <div className={Styles.datePickSideStyles}>
        <div className={Styles.fieldLabelStyles}>Chosen date</div>
        <div className={Styles.datePickChosenStyles}>{formatDayLong(chosenDate)}</div>
        <div className={Styles.datePickHintStyles}>Any date works, past or future. Today is ringed.</div>
        <div className={Styles.datePickActionsStyles}>
          <Button variant="primary" size="sm" disabled={isAnswering} onClick={() => onAnswer(chosenDate)}>
            Save for {formatDayShort(chosenDate)}
          </Button>
          <Button size="sm" disabled={isAnswering} onClick={() => setIsPicking(false)}>
            Back
          </Button>
        </div>
      </div>
    </div>
  );
};
