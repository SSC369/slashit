import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { buildExpense } from "../../../testing/expenseFixture";
import {
  ExpenseModelDownNote,
  ExpenseQuestionCard,
  ExpenseRefusedNote,
  ExpenseSavedCard,
} from "./ExpenseCards";

const questionProps = {
  pendingCaptureId: "pc-1",
  amountCandidates: [],
  readDate: null,
  answerDraft: "",
  isAnswering: false,
  onAnswerDraftChange: vi.fn(),
  onAnswerSubmit: vi.fn(),
  onAnswer: vi.fn(),
  onDiscard: vi.fn(),
};

describe("Expense capture cards, F-1 of sub-plan 4.1", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 2, 10, 0));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("reads back the four fields of a save (FR-12)", () => {
    render(<ExpenseSavedCard expense={buildExpense()} onEditExpense={vi.fn()} onOpenExpense={vi.fn()} />);

    expect(screen.getByText("Expense saved")).toBeInTheDocument();
    expect(screen.getByText("₹850")).toHaveAttribute("aria-label", "850 rupees");
    expect(screen.getByText("Dinner with friends")).toBeInTheDocument();
    expect(screen.getByText("Food")).toBeInTheDocument();
    expect(screen.getByText("Thu 1 Oct")).toBeInTheDocument();
  });

  it("writes today's date as Today", () => {
    render(
      <ExpenseSavedCard
        expense={buildExpense({ spentOn: "2026-10-02" })}
        onEditExpense={vi.fn()}
        onOpenExpense={vi.fn()}
      />,
    );

    expect(screen.getByText("Today")).toBeInTheDocument();
  });

  it("refuses another currency and an over-long description (FR-6, FR-13)", () => {
    const { rerender } = render(<ExpenseRefusedNote reason="FOREIGN_CURRENCY" length={null} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Slashit records rupees only for now.");

    rerender(<ExpenseRefusedNote reason="DESCRIPTION_TOO_LONG" length={236} />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "That description is 236 characters. It can be up to 200.",
    );
  });

  it("says the model is down without saving (FR-14)", () => {
    render(<ExpenseModelDownNote />);

    expect(screen.getByRole("alert")).toHaveTextContent("Its AI model is unavailable.");
  });

  it("asks for the amount with a typed answer (FR-3)", () => {
    const onAnswerSubmit = vi.fn();
    render(
      <ExpenseQuestionCard
        {...questionProps}
        kind="AMOUNT"
        question="How much was it?"
        answerDraft="850"
        onAnswerSubmit={onAnswerSubmit}
      />,
    );

    const field = screen.getByLabelText("Amount in rupees");
    expect(field).toHaveFocus();
    fireEvent.keyDown(field, { key: "Enter" });
    expect(onAnswerSubmit).toHaveBeenCalled();
  });

  it("asks what the expense was for (FR-4)", () => {
    render(<ExpenseQuestionCard {...questionProps} kind="DESCRIPTION" question="What was the expense for?" />);

    expect(screen.getByText("What was the expense for?")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("What it was for…")).toBeInTheDocument();
  });

  it("offers one chip per number and sends the paise picked (FR-5)", () => {
    const onAnswer = vi.fn();
    render(
      <ExpenseQuestionCard
        {...questionProps}
        kind="AMOUNT_CHOICE"
        question="Which number is the amount?"
        amountCandidates={["200", "18000"]}
        onAnswer={onAnswer}
      />,
    );

    expect(screen.getByText("Your text has two numbers. Nothing is saved until you pick one.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "2 rupees" })).toHaveFocus();
    fireEvent.click(screen.getByRole("button", { name: "180 rupees" }));
    expect(onAnswer).toHaveBeenCalledWith("18000");
  });

  it("confirms the date read, or picks another from the calendar (FR-8)", () => {
    const onAnswer = vi.fn();
    render(
      <ExpenseQuestionCard
        {...questionProps}
        kind="DATE"
        question="Next Saturday reads as Sat 10 Oct, which is after today. Save it for that date?"
        readDate="2026-10-10"
        onAnswer={onAnswer}
      />,
    );

    expect(screen.getByText("Sat 10 Oct").tagName).toBe("B");
    fireEvent.click(screen.getByRole("button", { name: /Yes, Sat 10 Oct/ }));
    expect(onAnswer).toHaveBeenLastCalledWith("2026-10-10");

    fireEvent.click(screen.getByRole("button", { name: /Pick another date/ }));
    fireEvent.click(screen.getByRole("gridcell", { name: "Saturday 3 October 2026" }));
    expect(screen.getByText("Saturday 3 October 2026", { selector: "div" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Save for Sat 3 Oct" }));
    expect(onAnswer).toHaveBeenLastCalledWith("2026-10-03");
  });
});
