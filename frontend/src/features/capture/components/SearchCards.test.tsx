import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { buildMemory } from "@/testing/memoryFixture";
import { buildSearchResults, buildTask } from "@/testing/searchFixture";
import { SearchLoadingCard, SearchResultsCard, SearchTooLongNote } from "./SearchCards";

/** Epic 005, sub-plan 4.1, C-16 (FR-7 to FR-10, FR-20). */
describe("SearchResultsCard", () => {
  it("groups records by type with a count, and opens a record", () => {
    const onOpenRecord = vi.fn();
    render(<SearchResultsCard results={buildSearchResults()} onOpenRecord={onOpenRecord} onSeeAll={vi.fn()} />);

    expect(screen.getByText(/2 records match/)).toBeInTheDocument();
    expect(screen.getByText("Memories")).toBeInTheDocument();
    expect(screen.getByText("Tasks")).toBeInTheDocument();
    expect(screen.getAllByText("1 match")).toHaveLength(2);

    fireEvent.click(screen.getByText("Renew passport"));
    expect(onOpenRecord).toHaveBeenCalledWith(expect.objectContaining({ __typename: "Task", id: "task-1" }));
  });

  it("shows See all when a group has more than it shows (FR-8)", () => {
    const onSeeAll = vi.fn();
    const tasks = Array.from({ length: 5 }, (_, index) => ({
      citation: null,
      record: { __typename: "Task" as const, ...buildTask({ id: `task-${index}`, title: `Task ${index}` }) },
    }));
    const results = buildSearchResults({
      query: "career",
      groups: [{ recordType: "TASK", total: 7, hits: tasks }],
    });

    render(<SearchResultsCard results={results} onOpenRecord={vi.fn()} onSeeAll={onSeeAll} />);
    fireEvent.click(screen.getByText(/See all 7 in Records/));

    expect(onSeeAll).toHaveBeenCalledWith("TASK", "career");
  });

  it("says nothing matched, and offers Records (FR-10)", () => {
    const onSeeAll = vi.fn();
    render(
      <SearchResultsCard
        results={buildSearchResults({ query: "kayak", groups: [] })}
        onOpenRecord={vi.fn()}
        onSeeAll={onSeeAll}
      />,
    );

    expect(screen.getByText(/No records match “kayak”/)).toBeInTheDocument();
    expect(screen.getByText("Nothing you have recorded matches by word or by meaning.")).toBeInTheDocument();
    fireEvent.click(screen.getByText(/Browse Records/));
    expect(onSeeAll).toHaveBeenCalledWith(null, "");
  });

  it("flags word-only results when meaning matching was unavailable (FR-20)", () => {
    render(
      <SearchResultsCard
        results={buildSearchResults({ meaningUnavailable: true })}
        onOpenRecord={vi.fn()}
        onSeeAll={vi.fn()}
      />,
    );

    expect(screen.getByText(/Showing word matches only/)).toBeInTheDocument();
  });

  it("shows a memory's category and a task's status", () => {
    const results = buildSearchResults({
      groups: [
        {
          recordType: "MEMORY",
          total: 1,
          hits: [{ citation: null, record: { __typename: "Memory", ...buildMemory({ category: "LIFE" }) } }],
        },
        {
          recordType: "TASK",
          total: 1,
          hits: [{ citation: null, record: { __typename: "Task", ...buildTask({ status: "DONE" }) } }],
        },
      ],
    });

    render(<SearchResultsCard results={results} onOpenRecord={vi.fn()} onSeeAll={vi.fn()} />);

    expect(screen.getByText("Life")).toBeInTheDocument();
    expect(screen.getByText("Done")).toBeInTheDocument();
  });
});

describe("SearchTooLongNote and SearchLoadingCard", () => {
  it("states the length and the limit (FR-3)", () => {
    render(<SearchTooLongNote length={612} limit={500} />);

    expect(screen.getByText("That is 612 characters.")).toBeInTheDocument();
    expect(screen.getByText(/A search can be up to 500/)).toBeInTheDocument();
  });

  it("explains the wait while searching", () => {
    render(<SearchLoadingCard />);

    expect(screen.getByText("Searching your records…")).toBeInTheDocument();
  });
});
