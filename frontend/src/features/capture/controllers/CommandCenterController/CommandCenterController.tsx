import { History } from "lucide-react";
import { observer } from "mobx-react-lite";
import { useEffect, useRef, useState, type ChangeEvent, type KeyboardEvent, type ReactElement } from "react";
import { useNavigate } from "react-router";

import type { SubmitCaptureCallbacks } from "../../../../api/mutations/SubmitCapture/responseHandler";
import useAnswerPendingCapture from "../../../../api/mutations/AnswerPendingCapture/useAnswerPendingCapture";
import useDiscardPendingCapture from "../../../../api/mutations/DiscardPendingCapture/useDiscardPendingCapture";
import useSubmitCapture from "../../../../api/mutations/SubmitCapture/useSubmitCapture";
import PageTopbar from "../../../../components/PageTopbar";
import { API_FETCHING } from "../../../../constants/apiConstants";
import {
  ARGUMENTLESS_COMMANDS,
  CAPTURE_COMMANDS,
  MEMORY_SAVE_COMMANDS,
} from "../../../../constants/captureCommands";
import type { RootStore } from "../../../../stores/RootStore";
import { useStore } from "../../../../stores/StoreProvider";
import { whenTextInSentence } from "../../../../utils/formatReminder";
import { useOnlineStatus } from "../../../../hooks/useOnlineStatus";
import CommandInputBar from "../../components/CommandInputBar";
import CommandPalette from "../../components/CommandPalette";
import EmptyState from "../../components/EmptyState";
import HistoryPanel from "../../components/HistoryPanel";
import TurnCard from "../../components/TurnCard";
import * as StreamStyles from "../../components/styles";
import * as Styles from "./styles";

const isPaletteOpen = (input: string): boolean => input.startsWith("/") && !input.includes(" ");

const isMemorySave = (said: string): boolean =>
  MEMORY_SAVE_COMMANDS.some((command) => said === command || said.startsWith(`${command} `));

interface CaptureResultTarget {
  store: RootStore;
  turnId: string;
  said: string;
  /** Puts what was typed back in the command bar, for the refusals whose
   * copy says "kept below". */
  restoreInput: (said: string) => void;
}

const buildCaptureResultCallbacks = (target: CaptureResultTarget): SubmitCaptureCallbacks => {
  const { store, turnId, said, restoreInput } = target;
  const captureStore = store.capture;
  // RemindModelDown: a /remind the model could not read keeps its own copy.
  // Every other command keeps 001's refusal card, unchanged.
  const refuseUnreadable = (message: string): void => {
    // Epic 004 FR-9: a memory save refused on the model keeps its own copy.
    if (isMemorySave(said)) {
      captureStore.resolveTurn(turnId, { status: "memoryModelDown" });
      restoreInput(said);
      return;
    }
    if (said.startsWith("/remind")) {
      captureStore.resolveTurn(turnId, { status: "modelDown" });
      restoreInput(said);
      return;
    }
    captureStore.resolveTurn(turnId, { status: "refused", message });
  };

  return {
    onTaskCreated: (task) => captureStore.resolveTurn(turnId, { status: "taskCreated", task }),
    onTasksListed: (tasks) => captureStore.resolveTurn(turnId, { status: "taskList", tasks }),
    onReminderCreated: (reminder) => {
      captureStore.resolveTurn(turnId, { status: "reminderCreated", reminder });
      store.reminders.upsert(reminder);
      store.toast.show({
        message: `Reminder set for ${whenTextInSentence(reminder.whenText)}`,
        linkLabel: "View in Records",
        linkTo: `/records/reminders/${reminder.id}`,
      });
    },
    onRemindersListed: (reminders) =>
      captureStore.resolveTurn(turnId, { status: "reminderList", reminders }),
    onReminderLimitReached: ({ limit }) => {
      captureStore.resolveTurn(turnId, { status: "reminderLimit", limit });
      restoreInput(said);
    },
    onMemorySaved: ({ memory, secretCaution }) => {
      captureStore.resolveTurn(turnId, { status: "memorySaved", memory, secretCaution });
      store.memories.upsert(memory);
    },
    onMemoriesListed: ({ memories, searchText }) =>
      captureStore.resolveTurn(turnId, { status: "memoryList", memories, searchText }),
    onMemoryTooLong: ({ length, limit }) => {
      captureStore.resolveTurn(turnId, { status: "memoryTooLong", length, limit });
      restoreInput(said);
    },
    onPendingQuestionCreated: ({ pendingCaptureId, question }) =>
      captureStore.resolveTurn(turnId, { status: "pending", pendingCaptureId, question, answerDraft: "" }),
    onNonCommandGuidance: (originalInput) =>
      captureStore.resolveTurn(turnId, { status: "nonCommand", originalInput }),
    onUnrecognisedCommand: ({ attemptedName, closestMatches }) =>
      captureStore.resolveTurn(turnId, { status: "unrecognisedCommand", attemptedName, closestMatches }),
    onUserLimitReached: ({ message }) => captureStore.resolveTurn(turnId, { status: "refused", message }),
    onProviderUnavailable: refuseUnreadable,
    onProviderTimeout: ({ message }) => refuseUnreadable(message),
    onSharedQuotaExhausted: refuseUnreadable,
    onMalformedResult: ({ message }) => refuseUnreadable(message),
  };
};

const filterCommands = (input: string) => {
  const query = input.slice(1).toLowerCase();
  return CAPTURE_COMMANDS.filter((command) => command.name.slice(1).includes(query));
};

const CommandCenterController = (): ReactElement => {
  const store = useStore();
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [submittingTurnId, setSubmittingTurnId] = useState<string | null>(null);
  const isOnline = useOnlineStatus();

  const { triggerAPI: triggerSubmitCapture } = useSubmitCapture();
  const {
    triggerAPI: triggerAnswerPendingCapture,
    apiStatus: answerApiStatus,
  } = useAnswerPendingCapture();
  const { triggerAPI: triggerDiscardPendingCapture } = useDiscardPendingCapture();

  const paletteOpen = isPaletteOpen(input);
  const matches = paletteOpen ? filterCommands(input) : [];
  const boundedSelectedIndex = Math.min(selectedIndex, Math.max(matches.length - 1, 0));

  // Only into an empty bar: something typed since the request left wins.
  const restoreInput = (said: string): void => {
    setInput((current) => (current === "" ? said : current));
  };

  const submit = (rawInput: string): void => {
    const text = rawInput.trim();
    if (!text || !isOnline) return;

    const turnId = store.capture.addLoadingTurn(text);
    triggerSubmitCapture({
      rawInput: text,
      ...buildCaptureResultCallbacks({ store, turnId, said: text, restoreInput }),
      onRequestFailed: (requestError) =>
        store.capture.resolveTurn(turnId, { status: "refused", message: requestError.message }),
    });
  };

  const handleInputChange = (event: ChangeEvent<HTMLInputElement>): void => {
    setInput(event.target.value);
    setSelectedIndex(0);
  };

  const pickCommand = (name: string): void => {
    setInput(`${name} `);
    setSelectedIndex(0);
  };

  const handleFillCommand = (name: string): void => {
    if (ARGUMENTLESS_COMMANDS.includes(name)) {
      submit(name);
      return;
    }
    pickCommand(name);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>): void => {
    if (event.key === "Escape") {
      event.preventDefault();
      setInput("");
      setSelectedIndex(0);
      return;
    }

    if (paletteOpen) {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        if (matches.length) setSelectedIndex((boundedSelectedIndex + 1) % matches.length);
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        if (matches.length) setSelectedIndex((boundedSelectedIndex - 1 + matches.length) % matches.length);
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        if (matches.length) pickCommand(matches[boundedSelectedIndex].name);
        return;
      }
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      // Clear before submitting, so a refusal that puts the command back in
      // the bar is not wiped by this clear landing after it.
      setInput("");
      submit(input);
    }
  };

  const handleAnswerDraftChange = (turnId: string, draft: string): void => {
    store.capture.setAnswerDraft(turnId, draft);
  };

  const handleAnswerSubmit = (turnId: string): void => {
    const turn = store.capture.turns.get(turnId);
    if (!turn || turn.status !== "pending") return;
    const answer = turn.answerDraft.trim();
    if (!answer || !isOnline) return;

    setSubmittingTurnId(turnId);
    triggerAnswerPendingCapture({
      pendingCaptureId: turn.pendingCaptureId,
      answer,
      ...buildCaptureResultCallbacks({ store, turnId, said: turn.said, restoreInput }),
      onRequestFailed: (requestError) =>
        store.capture.resolveTurn(turnId, { status: "refused", message: requestError.message }),
    });
  };

  const handleQuickAnswer = (turnId: string, answer: string): void => {
    store.capture.setAnswerDraft(turnId, answer);
    handleAnswerSubmit(turnId);
  };

  const handleDiscardPending = (turnId: string): void => {
    const turn = store.capture.turns.get(turnId);
    if (!turn || turn.status !== "pending") return;
    triggerDiscardPendingCapture({
      pendingCaptureId: turn.pendingCaptureId,
      onDiscarded: () => store.capture.removeTurn(turnId),
    });
  };

  const handleUseWithAddTask = (originalInput: string): void => {
    setInput(`/add-task ${originalInput} `);
  };

  const handleRetry = (said: string): void => {
    // The refusal put the command back in the bar; running it again empties it.
    setInput((current) => (current === said ? "" : current));
    submit(said);
  };

  const handleOpenReminder = (id: string): void => {
    navigate(`/records/reminders/${id}`);
  };

  const handleEditReminder = (id: string): void => {
    navigate(`/records/reminders/${id}/edit`);
  };

  const handleOpenReminders = (): void => {
    store.records.setKindFilter("REMINDERS");
    navigate("/records");
  };

  const handleOpenMemory = (id: string): void => {
    navigate(`/records/memories/${id}`);
  };

  const handleEditMemory = (id: string): void => {
    navigate(`/records/memories/${id}/edit`);
  };

  const handleOpenMemories = (): void => {
    store.records.setKindFilter("MEMORIES");
    navigate("/records");
  };

  const turns = store.capture.getAll();
  const showEmpty = turns.length === 0 && !input;
  const streamRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const streamElement = streamRef.current;
    if (!streamElement) return;
    streamElement.scrollTop = streamElement.scrollHeight;
  }, [turns.length]);

  return (
    <div className={Styles.pageStyles}>
      <PageTopbar
        title="Capture"
        actions={
          <button
            type="button"
            aria-label="Capture history"
            className={Styles.historyButtonStyles}
            onClick={() => setIsHistoryOpen(true)}
          >
            <History size={17} />
          </button>
        }
      />

      <HistoryPanel isOpen={isHistoryOpen} onClose={() => setIsHistoryOpen(false)} />

      {showEmpty ? (
        <EmptyState onFillCommand={handleFillCommand} />
      ) : (
        <div ref={streamRef} className={StreamStyles.streamContainerStyles}>
          <div className={StreamStyles.streamColumnStyles}>
            {turns.map((turn) => (
              <TurnCard
                key={turn.id}
                turn={turn}
                isAnswering={submittingTurnId === turn.id && answerApiStatus === API_FETCHING}
                onAnswerDraftChange={handleAnswerDraftChange}
                onAnswerSubmit={handleAnswerSubmit}
                onQuickAnswer={handleQuickAnswer}
                onDiscardPending={handleDiscardPending}
                onUseWithAddTask={handleUseWithAddTask}
                onRetry={handleRetry}
                onEditReminder={handleEditReminder}
                onOpenReminder={handleOpenReminder}
                onOpenReminders={handleOpenReminders}
                onEditMemory={handleEditMemory}
                onOpenMemory={handleOpenMemory}
                onOpenMemories={handleOpenMemories}
              />
            ))}
          </div>
        </div>
      )}

      <div className={StreamStyles.dockStyles}>
        <div className={StreamStyles.inputWrapStyles}>
          {paletteOpen && (
            <CommandPalette
              matches={matches}
              selectedIndex={boundedSelectedIndex}
              countLabel={
                input.length > 1
                  ? `${matches.length} of ${CAPTURE_COMMANDS.length} match "${input.slice(1)}"`
                  : `${CAPTURE_COMMANDS.length} available`
              }
              onPick={pickCommand}
            />
          )}
          <CommandInputBar
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={!isOnline}
          />
        </div>
        <div className={StreamStyles.hintRowStyles}>
          <span>
            <span className={StreamStyles.kbdStyles}>/</span> commands
          </span>
          <span>
            <span className={StreamStyles.kbdStyles}>Enter</span> run
          </span>
          <span>
            <span className={StreamStyles.kbdStyles}>Esc</span> dismiss
          </span>
        </div>
      </div>
    </div>
  );
};

export default observer(CommandCenterController);
