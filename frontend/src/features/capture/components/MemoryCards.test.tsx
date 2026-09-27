import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { buildMemory } from "../../../testing/memoryFixture";
import { MemoryListCard, MemoryModelDownNote, MemorySavedCard, MemoryTooLongNote } from "./MemoryCards";

describe("Memory capture cards, F-1 of sub-plan 4.1", () => {
  it("shows the saved fact and its category, with no caution by default (FR-7)", () => {
    render(
      <MemorySavedCard memory={buildMemory()} secretCaution={null} onEditMemory={vi.fn()} onOpenMemory={vi.fn()} />,
    );

    expect(screen.getByText("Memory saved")).toBeInTheDocument();
    expect(screen.getByText("My passport expires in 2030")).toBeInTheDocument();
    expect(screen.getByText("Life")).toBeInTheDocument();
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });

  it("names the kind of secret in the caution, never blocking the save (FR-8)", () => {
    render(
      <MemorySavedCard
        memory={buildMemory({ text: "Locker PIN 4417" })}
        secretCaution="CREDENTIAL"
        onEditMemory={vi.fn()}
        onOpenMemory={vi.fn()}
      />,
    );

    expect(screen.getByRole("note")).toHaveTextContent("This looks like a password or PIN.");
    expect(screen.getByText("Memory saved")).toBeInTheDocument();
  });

  it("marks an uncategorised memory with the dashed tag (FR-6)", () => {
    render(
      <MemorySavedCard
        memory={buildMemory({ category: null })}
        secretCaution={null}
        onEditMemory={vi.fn()}
        onOpenMemory={vi.fn()}
      />,
    );

    expect(screen.getByText("No category")).toBeInTheDocument();
  });

  it("lists matches for a lookup and opens one on click (FR-20)", () => {
    const onOpenMemory = vi.fn();
    render(
      <MemoryListCard
        memories={[buildMemory({ id: "m-2", text: "Career goal: backend engineer" })]}
        searchText="career"
        onOpenMemory={onOpenMemory}
        onOpenMemories={vi.fn()}
      />,
    );

    expect(screen.getByText("1 memory match “career”")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Career goal: backend engineer"));
    expect(onOpenMemory).toHaveBeenCalledWith("m-2");
  });

  it("says a lookup matched nothing and that matching is by word", () => {
    render(<MemoryListCard memories={[]} searchText="visa" onOpenMemory={vi.fn()} onOpenMemories={vi.fn()} />);

    expect(screen.getByText("No memories match “visa”")).toBeInTheDocument();
    expect(screen.getByText(/Matching is by word/)).toBeInTheDocument();
  });

  it("states the length and the limit when a fact is too long (FR-4)", () => {
    render(<MemoryTooLongNote length={612} limit={500} />);

    expect(screen.getByText("That is 612 characters. A memory can be up to 500.")).toBeInTheDocument();
  });

  it("offers a retry when the model is down (FR-9)", () => {
    const onRetry = vi.fn();
    render(<MemoryModelDownNote onRetry={onRetry} />);

    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(onRetry).toHaveBeenCalled();
  });
});
