import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { buildMemory } from "../../../testing/memoryFixture";
import { ConflictCard } from "./ConflictCard";

const emirates = buildMemory({ id: "m1", text: "Preferred airline is Emirates", category: "PERSONAL" });
const onlyEmirates = buildMemory({ id: "m2", text: "I only fly Emirates", category: null });

const renderCard = (overrides: Partial<Parameters<typeof ConflictCard>[0]> = {}) => {
  const props = {
    newText: "My preferred airline is Qatar Airways",
    conflicting: [emirates],
    deferred: false,
    error: null,
    isBusy: false,
    onAnswer: vi.fn(),
    onDecideLater: vi.fn(),
    onReopen: vi.fn(),
    ...overrides,
  };
  render(<ConflictCard {...props} />);
  return props;
};

describe("ConflictCard, F-3.1 and F-3.4 of sub-plan 4.3", () => {
  it("shows the new fact beside every old one, with focus on Keep the new one", () => {
    renderCard({ conflicting: [emirates, onlyEmirates] });

    const card = screen.getByRole("group", { name: "Which is correct?" });
    expect(within(card).getByLabelText("New")).toHaveTextContent("My preferred airline is Qatar Airways");
    expect(within(card).getAllByLabelText("Saved before")).toHaveLength(2);
    expect(screen.getByText("This contradicts 2 memories you already have.")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Keep the new one" })).toHaveFocus();
  });

  it("names every memory Keep the new one forgets (FR-12)", () => {
    renderCard({ conflicting: [emirates, onlyEmirates] });

    const keepNew = screen.getByRole("radio", { name: "Keep the new one" }).closest("label");
    expect(keepNew).toHaveTextContent(
      "Saves the new memory and forgets Preferred airline is Emirates and I only fly Emirates for good.",
    );
  });

  it("sends the chosen answer; the button names it", () => {
    const props = renderCard();

    fireEvent.click(screen.getByRole("radio", { name: "Both are correct" }));
    fireEvent.click(screen.getByRole("button", { name: "Both are correct" }));

    expect(props.onAnswer).toHaveBeenCalledWith("BOTH");
  });

  it("Decide later sends nothing, and the folded card reopens", () => {
    const props = renderCard();
    fireEvent.click(screen.getByRole("button", { name: "Decide later" }));
    expect(props.onDecideLater).toHaveBeenCalled();
    expect(props.onAnswer).not.toHaveBeenCalled();

    const folded = renderCard({ deferred: true });
    fireEvent.click(screen.getByRole("button", { name: "Answer now" }));
    expect(folded.onReopen).toHaveBeenCalled();
  });

  it("stacks the pair and the actions below the small breakpoint (Design §5)", () => {
    renderCard();

    const pair = screen.getByLabelText("New").parentElement;
    expect(pair?.className).toContain("grid-cols-1");
    expect(pair?.className).toContain("sm:grid-cols-2");
    const actions = screen.getByRole("button", { name: "Decide later" }).parentElement;
    expect(actions?.className).toContain("flex-col-reverse");
  });
});
