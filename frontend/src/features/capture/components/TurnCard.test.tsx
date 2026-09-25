import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { CaptureTurn } from "../../../stores/CaptureStore";
import TurnCard from "./TurnCard";

const pendingTurn: CaptureTurn = {
  id: "turn-1",
  said: "/add-task",
  status: "pending",
  pendingCaptureId: "pc-1",
  question: "What should the task be called?",
  answerDraft: "Buy milk",
};

const baseProps = {
  onAnswerDraftChange: vi.fn(),
  onAnswerSubmit: vi.fn(),
  onQuickAnswer: vi.fn(),
  onDiscardPending: vi.fn(),
  onUseWithAddTask: vi.fn(),
  onRetry: vi.fn(),
  onEditReminder: vi.fn(),
  onOpenReminder: vi.fn(),
  onOpenReminders: vi.fn(),
  onEditMemory: vi.fn(),
  onOpenMemory: vi.fn(),
  onOpenMemories: vi.fn(),
  onForgetSelect: vi.fn(),
  onForgetContinue: vi.fn(),
  onForgetConfirm: vi.fn(),
  onForgetCancel: vi.fn(),
};

describe("TurnCard", () => {
  it("T-4.10: disables the answer input and shows a spinner when isAnswering", () => {
    render(<TurnCard turn={pendingTurn} isAnswering {...baseProps} />);

    expect(screen.getByPlaceholderText("Type an answer…")).toBeDisabled();
    expect(screen.getByRole("status", { name: "Saving" })).toBeInTheDocument();
  });

  it("T-4.10: leaves the answer input enabled and shows no spinner when not answering", () => {
    render(<TurnCard turn={pendingTurn} {...baseProps} />);

    expect(screen.getByPlaceholderText("Type an answer…")).not.toBeDisabled();
    expect(screen.queryByRole("status", { name: "Saving" })).not.toBeInTheDocument();
  });
});
