import { AlertCircle, Check, Clock } from "lucide-react";
import type { ReactElement } from "react";

import InlineSpinner from "../../../components/InlineSpinner";
import Button from "../../../design-system/components/Button";
import type { CaptureTurn } from "../../../stores/CaptureStore";
import { formatShortDate as formatDueDate } from "../../../utils/formatDate";
import {
  MemoryListCard,
  MemoryModelDownNote,
  MemorySavedCard,
  MemoryTooLongNote,
} from "./MemoryCards";
import { ReminderCreatedCard, ReminderListCard } from "./ReminderCards";
import * as Styles from "./styles";

interface TurnCardProps {
  turn: CaptureTurn;
  isAnswering?: boolean;
  onAnswerDraftChange: (id: string, draft: string) => void;
  onAnswerSubmit: (id: string) => void;
  onQuickAnswer: (id: string, answer: string) => void;
  onDiscardPending: (id: string) => void;
  onUseWithAddTask: (said: string) => void;
  onRetry: (said: string) => void;
  onEditReminder: (id: string) => void;
  onOpenReminder: (id: string) => void;
  onOpenReminders: () => void;
  onEditMemory: (id: string) => void;
  onOpenMemory: (id: string) => void;
  onOpenMemories: () => void;
}

/** `RemindAsk`'s ready answers: one tap instead of typing a time. */
const REMIND_QUICK_ANSWERS = ["In 1 hour", "This evening, 7:00 PM", "Tomorrow, 9:00 AM"];

const isRemindCommand = (said: string): boolean => said.startsWith("/remind ") || said === "/remind";

const assertNever = (value: never): never => {
  throw new Error(`Unhandled capture turn status: ${JSON.stringify(value)}`);
};

const TurnCard = (props: TurnCardProps): ReactElement => {
  const { turn } = props;

  return (
    <div className={Styles.turnStyles}>
      <div className={Styles.saidRowStyles}>
        <div className={Styles.saidBoxStyles}>{turn.said}</div>
      </div>
      <TurnBody {...props} />
    </div>
  );
};

const TurnBody = (props: TurnCardProps): ReactElement => {
  const {
    turn,
    isAnswering = false,
    onAnswerDraftChange,
    onAnswerSubmit,
    onQuickAnswer,
    onDiscardPending,
    onUseWithAddTask,
    onRetry,
    onEditReminder,
    onOpenReminder,
    onOpenReminders,
    onEditMemory,
    onOpenMemory,
    onOpenMemories,
  } = props;
  const isRemind = isRemindCommand(turn.said);

  switch (turn.status) {
    case "loading":
      return (
        <div className={Styles.cardStyles}>
          <div className={Styles.cardHeadStyles}>
            <span className={`${Styles.pillBaseStyles} ${Styles.pillWaitStyles}`}>
              <Clock size={13} /> Reading your command
            </span>
          </div>
          <div className={Styles.fieldsGridStyles}>
            <div className={Styles.fieldCellStyles}>
              <span className={Styles.fieldLabelStyles}>{isRemind ? "Reminder" : "Task"}</span>
              <div className="mt-1 h-[11px] w-[78%] animate-pulse rounded bg-border" />
            </div>
            <div className={Styles.fieldCellStyles}>
              <span className={Styles.fieldLabelStyles}>{isRemind ? "When" : "Due"}</span>
              <div className="mt-1 h-[11px] w-[56%] animate-pulse rounded bg-border" />
            </div>
            <div className={Styles.fieldCellStyles}>
              <span className={Styles.fieldLabelStyles}>{isRemind ? "Repeat" : "Status"}</span>
              <div className="mt-1 h-[11px] w-[44%] animate-pulse rounded bg-border" />
            </div>
          </div>
          <div className={Styles.cardFootStyles}>
            <span>Nothing is saved until every field is read</span>
          </div>
        </div>
      );

    case "taskCreated":
      return (
        <div className={Styles.cardStyles}>
          <div className={Styles.cardHeadStyles}>
            <span className={`${Styles.pillBaseStyles} ${Styles.pillDoneStyles}`}>
              <Check size={13} /> Task created
            </span>
          </div>
          <div className={Styles.fieldsGridStyles}>
            <div className={Styles.fieldCellStyles}>
              <span className={Styles.fieldLabelStyles}>Task</span>
              <span className={Styles.fieldValueStyles}>{turn.task.title}</span>
            </div>
            <div className={Styles.fieldCellStyles}>
              <span className={Styles.fieldLabelStyles}>Due</span>
              <span className={Styles.fieldValueStyles}>{formatDueDate(turn.task.dueAt)}</span>
            </div>
            <div className={Styles.fieldCellStyles}>
              <span className={Styles.fieldLabelStyles}>Status</span>
              <span className={Styles.fieldValueStyles}>{turn.task.status}</span>
            </div>
          </div>
          <div className={Styles.cardFootStyles}>
            <span>Created just now · via command</span>
          </div>
        </div>
      );

    case "taskList":
      return (
        <div className={Styles.cardStyles}>
          <div className={Styles.cardHeadStyles}>
            <span className={`${Styles.pillBaseStyles} ${Styles.pillDoneStyles}`}>
              <Check size={13} /> {turn.tasks.length} open {turn.tasks.length === 1 ? "task" : "tasks"}
            </span>
          </div>
          <div className="py-1.5">
            {turn.tasks.map((task) => (
              <div key={task.id} className={Styles.taskListRowStyles}>
                <span>{task.title}</span>
                <span className={Styles.taskListDueStyles}>{formatDueDate(task.dueAt)}</span>
              </div>
            ))}
          </div>
        </div>
      );

    case "reminderCreated":
      return (
        <ReminderCreatedCard
          reminder={turn.reminder}
          onEditReminder={onEditReminder}
          onOpenReminder={onOpenReminder}
        />
      );

    case "reminderList":
      return (
        <ReminderListCard
          reminders={turn.reminders}
          onOpenReminder={onOpenReminder}
          onOpenReminders={onOpenReminders}
        />
      );

    case "reminderLimit":
      return (
        <div className={`${Styles.noteBaseStyles} ${Styles.noteErrStyles}`}>
          <AlertCircle size={18} className="shrink-0 text-destructive" />
          <div className="flex-1">
            <div className={Styles.noteTitleStyles}>
              You have {turn.limit} active reminders, the most Slashit holds.
            </div>
            <div className={Styles.noteBodyStyles}>
              Mark one done or delete one, then try again. What you typed is kept below.
            </div>
          </div>
        </div>
      );

    case "memorySaved":
      return (
        <MemorySavedCard
          memory={turn.memory}
          secretCaution={turn.secretCaution}
          onEditMemory={onEditMemory}
          onOpenMemory={onOpenMemory}
        />
      );

    case "memoryList":
      return (
        <MemoryListCard
          memories={turn.memories}
          searchText={turn.searchText}
          onOpenMemory={onOpenMemory}
          onOpenMemories={onOpenMemories}
        />
      );

    case "memoryTooLong":
      return <MemoryTooLongNote length={turn.length} limit={turn.limit} />;

    case "memoryModelDown":
      return <MemoryModelDownNote onRetry={() => onRetry(turn.said)} />;

    case "modelDown":
      return (
        <div className={`${Styles.noteBaseStyles} ${Styles.noteErrStyles}`}>
          <AlertCircle size={18} className="shrink-0 text-destructive" />
          <div className="flex-1">
            <span className={`${Styles.pillBaseStyles} ${Styles.pillErrStyles}`}>Not saved</span>
            <div className={`${Styles.noteTitleStyles} mt-2`}>Slashit can't read that right now</div>
            <div className={Styles.noteBodyStyles}>
              Nothing was saved and nothing was half-saved. Your command is kept below. This clears
              on its own, usually within a few minutes.
            </div>
            <div className={Styles.noteActionsRowStyles}>
              <Button variant="primary" size="sm" onClick={() => onRetry(turn.said)}>
                Try again
              </Button>
            </div>
          </div>
        </div>
      );

    case "pending":
      return (
        <div className={Styles.pendingCardStyles}>
          <div className={Styles.pendingHeadStyles}>
            <span className={`${Styles.pillBaseStyles} ${Styles.pillWaitStyles}`}>
              <Clock size={13} /> {isRemind ? "One question" : "Waiting on you"}
            </span>
            <span className="ml-auto text-xs text-foreground-tertiary">
              Asked just now · nothing saved yet
            </span>
          </div>
          <div className={Styles.pendingBodyStyles}>
            <div className={Styles.pendingQuestionStyles}>{turn.question}</div>
            <div className={Styles.pendingHintStyles}>
              {isRemind
                ? "Reply with a day or time. Nothing is saved until you answer."
                : "You can answer this whenever you like. Leave it and nothing is recorded."}
            </div>
            {isRemind && (
              <div className={Styles.quickAnswerRowStyles}>
                {REMIND_QUICK_ANSWERS.map((answer) => (
                  <Button
                    key={answer}
                    size="sm"
                    disabled={isAnswering}
                    onClick={() => onQuickAnswer(turn.id, answer)}
                  >
                    {answer}
                  </Button>
                ))}
              </div>
            )}
            <div className={Styles.pendingAnswerRowStyles}>
              <div className={Styles.pendingAnswerFieldStyles}>
                <input
                  className={Styles.pendingAnswerInputStyles}
                  type="text"
                  placeholder="Type an answer…"
                  value={turn.answerDraft}
                  disabled={isAnswering}
                  onChange={(event) => onAnswerDraftChange(turn.id, event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key !== "Enter") return;
                    event.preventDefault();
                    onAnswerSubmit(turn.id);
                  }}
                />
                {isAnswering && <InlineSpinner className="mr-2.5 shrink-0" />}
              </div>
              <Button onClick={() => onDiscardPending(turn.id)} disabled={isAnswering}>
                Discard
              </Button>
            </div>
          </div>
        </div>
      );

    case "nonCommand":
      return (
        <div className={`${Styles.noteBaseStyles} ${Styles.noteWarnStyles}`}>
          <AlertCircle size={18} className="shrink-0 text-command" />
          <div className="flex-1">
            <div className={Styles.noteTitleStyles}>Slashit records through commands</div>
            <div className={Styles.noteBodyStyles}>
              Nothing was recorded. Your text is kept below, so you can send it with a command
              instead of typing it again.
            </div>
            <div className={Styles.noteInputEchoStyles}>{turn.originalInput}</div>
            <div className={Styles.noteActionsRowStyles}>
              <Button variant="primary" size="sm" onClick={() => onUseWithAddTask(turn.originalInput)}>
                Use with /add-task
              </Button>
            </div>
          </div>
        </div>
      );

    case "unrecognisedCommand":
      return (
        <div className={`${Styles.noteBaseStyles} ${Styles.noteWarnStyles}`}>
          <AlertCircle size={18} className="shrink-0 text-command" />
          <div className="flex-1">
            <div className={Styles.noteTitleStyles}>“{turn.attemptedName}” is not a command Slashit knows</div>
            {turn.closestMatches.length > 0 && (
              <div className={Styles.noteBodyStyles}>Did you mean {turn.closestMatches.join(", ")}?</div>
            )}
          </div>
        </div>
      );

    case "refused":
      return (
        <div className={`${Styles.noteBaseStyles} ${Styles.noteErrStyles}`}>
          <AlertCircle size={18} className="shrink-0 text-destructive" />
          <div className="flex-1">
            <div className={Styles.noteTitleStyles}>{turn.message}</div>
            <div className={Styles.noteBodyStyles}>
              Nothing was saved and nothing was half-saved. Your command is kept below.
            </div>
            <div className={Styles.noteInputEchoStyles}>{turn.said}</div>
            <div className={Styles.noteActionsRowStyles}>
              <Button variant="primary" size="sm" onClick={() => onRetry(turn.said)}>
                Try again
              </Button>
            </div>
          </div>
        </div>
      );

    default:
      return assertNever(turn);
  }
};

export default TurnCard;
