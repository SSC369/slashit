import { fireEvent, render, screen } from "@testing-library/react";
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
  onEditExpense: vi.fn(),
  onOpenExpense: vi.fn(),
  onOpenExpenseSummary: vi.fn(),
  onForgetSelect: vi.fn(),
  onForgetContinue: vi.fn(),
  onForgetConfirm: vi.fn(),
  onForgetCancel: vi.fn(),
  onConflictAnswer: vi.fn(),
  onConflictDefer: vi.fn(),
  onOpenSearchRecord: vi.fn(),
  onSeeAllSearch: vi.fn(),
  onOpenEvent: vi.fn(),
  onOpenEvents: vi.fn(),
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

  it("004 P-4: a memory save loads with Memory and Category, not task fields", () => {
    render(<TurnCard turn={{ id: "t-2", said: "/remember Blood group O+", status: "loading" }} {...baseProps} />);

    expect(screen.getByText("Memory")).toBeInTheDocument();
    expect(screen.getByText("Category")).toBeInTheDocument();
    expect(screen.queryByText("Task")).not.toBeInTheDocument();
  });

  it.each(["/memories passport"])("004 P-4: %s loads with no fields", (said) => {
    render(<TurnCard turn={{ id: "t-3", said, status: "loading" }} {...baseProps} />);

    expect(screen.getByText(/Reading your command/)).toBeInTheDocument();
    expect(screen.queryByText("Task")).not.toBeInTheDocument();
    expect(screen.queryByText("Memory")).not.toBeInTheDocument();
  });

  it("007 T-1.6: an event's date question offers the drawn answers (EventAsk, FR-2)", () => {
    const onQuickAnswer = vi.fn();
    const turn: CaptureTurn = {
      id: "t-4",
      said: "/add-event Dentist appointment",
      status: "pending",
      pendingCaptureId: "pc-4",
      question: "When is “Dentist appointment”?",
      answerDraft: "",
    };
    render(<TurnCard turn={turn} {...baseProps} onQuickAnswer={onQuickAnswer} />);

    fireEvent.click(screen.getByRole("button", { name: "This Saturday" }));

    expect(screen.getByText("One question")).toBeInTheDocument();
    expect(screen.getByText(/Reply with a date, and a time if there is one/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pick a date" })).toBeInTheDocument();
    expect(onQuickAnswer).toHaveBeenCalledWith("t-4", "This Saturday");
  });

  it("007: an event save loads with the saving pill, /events with date boxes", () => {
    const { unmount } = render(
      <TurnCard turn={{ id: "t-5", said: "/add-event Dentist Friday 4pm", status: "loading" }} {...baseProps} />,
    );
    expect(screen.getByText(/Saving event/)).toBeInTheDocument();
    unmount();

    render(<TurnCard turn={{ id: "t-6", said: "/events", status: "loading" }} {...baseProps} />);
    expect(screen.queryByText(/Saving event/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Reading your command/)).not.toBeInTheDocument();
  });
});
