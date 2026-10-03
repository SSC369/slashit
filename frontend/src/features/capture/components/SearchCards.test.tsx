import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { buildEvent } from "@/testing/eventFixture";
import { buildMemory } from "@/testing/memoryFixture";
import { buildAnsweredResults, buildSearchResults, buildTask } from "@/testing/searchFixture";
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
    expect(onOpenRecord).toHaveBeenCalledWith(
      expect.objectContaining({ __typename: "Task", id: "task-1" }),
      { kind: "SEARCH_RESULT_OPENED", position: 2 },
    );
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
    render(<SearchLoadingCard isQuestion={false} />);

    expect(screen.getByText("Searching your records…")).toBeInTheDocument();
  });

  it("explains a question's longer wait (NFR-4)", () => {
    render(<SearchLoadingCard isQuestion />);

    expect(screen.getByText("Reading your records to answer…")).toBeInTheDocument();
  });
});

/** Epic 005, sub-plan 4.2, C-2.14 (FR-15 to FR-19). */
describe("SearchResultsCard with a question", () => {
  it("shows the answer above the groups, with markers on sentences and rows (FR-16, FR-17)", () => {
    render(<SearchResultsCard results={buildAnsweredResults()} onOpenRecord={vi.fn()} onSeeAll={vi.fn()} />);

    expect(screen.getByText(/2 records found · 1 answer/)).toBeInTheDocument();
    const answer = screen.getByRole("region", { name: "Answer from your records" });
    expect(answer).toHaveTextContent("Your passport expires in 2030.1 You also have a pending task to renew it.2");
    expect(screen.getByRole("button", { name: /^source 1: / })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "source 2: Renew passport" })).toBeInTheDocument();
    expect(screen.getByLabelText("cited as 1")).toBeInTheDocument();
    expect(screen.getByLabelText("cited as 2")).toBeInTheDocument();
  });

  it("opens the cited record from a marker, recorded as that citation", () => {
    const onOpenRecord = vi.fn();
    render(<SearchResultsCard results={buildAnsweredResults()} onOpenRecord={onOpenRecord} onSeeAll={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: "source 2: Renew passport" }));

    expect(onOpenRecord).toHaveBeenCalledWith(
      expect.objectContaining({ __typename: "Task", id: "task-1" }),
      { kind: "ANSWER_CITATION_OPENED", position: 2 },
    );
  });

  it("opens a row from the keyboard", () => {
    const onOpenRecord = vi.fn();
    render(<SearchResultsCard results={buildAnsweredResults()} onOpenRecord={onOpenRecord} onSeeAll={vi.fn()} />);

    const [firstRow] = screen.getAllByRole("button", { name: /cited as 1/ });
    fireEvent.keyDown(firstRow, { key: "Enter" });

    expect(onOpenRecord).toHaveBeenCalledWith(expect.objectContaining({ __typename: "Memory" }), {
      kind: "SEARCH_RESULT_OPENED",
      position: 1,
    });
  });

  it("says nothing answers, invents nothing, and still lists loose matches (FR-18)", () => {
    const results = buildSearchResults({ query: "what is my blood type?", noSupport: true });
    render(<SearchResultsCard results={results} onOpenRecord={vi.fn()} onSeeAll={vi.fn()} />);

    expect(screen.getByText("No answer in your records")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Answer from your records" })).toHaveTextContent(
      "Nothing you have saved answers “what is my blood type?”. Save it with /remember and Slashit can answer next time.",
    );
    expect(screen.queryByLabelText(/cited as/)).not.toBeInTheDocument();
    expect(screen.getByText("Renew passport")).toBeInTheDocument();
  });

  it("says nothing answers when nothing matched at all (FR-18)", () => {
    const results = buildSearchResults({ query: "what is my blood type?", noSupport: true, groups: [] });
    render(<SearchResultsCard results={results} onOpenRecord={vi.fn()} onSeeAll={vi.fn()} />);

    expect(screen.getByText("No answer in your records")).toBeInTheDocument();
    expect(screen.getByText(/Nothing you have saved answers/)).toBeInTheDocument();
    expect(screen.queryByText(/Nothing you have recorded matches/)).not.toBeInTheDocument();
  });

  it("keeps the records and shows the amber line when the answer is unavailable (FR-19)", () => {
    const results = buildSearchResults({ query: "when does my passport expire?", answerUnavailable: true });
    render(<SearchResultsCard results={results} onOpenRecord={vi.fn()} onSeeAll={vi.fn()} />);

    expect(screen.getByText("2 records found", { exact: false })).not.toHaveTextContent("answer");
    expect(screen.getByText(/No answer this time: Slashit’s AI model is unavailable/)).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Answer from your records" })).not.toBeInTheDocument();
    expect(screen.getByText("Renew passport")).toBeInTheDocument();
  });

  it("names the daily limit when that is why the answer was refused (dev log Q7)", () => {
    const results = buildSearchResults({
      query: "when does my passport expire?",
      answerUnavailable: true,
      answerLimitReached: true,
    });
    render(<SearchResultsCard results={results} onOpenRecord={vi.fn()} onSeeAll={vi.fn()} />);

    expect(screen.getByText(/You have used today’s AI answers/)).toBeInTheDocument();
    expect(screen.queryByText(/AI model is unavailable/)).not.toBeInTheDocument();
    expect(screen.getByText("Renew passport")).toBeInTheDocument();
  });

  it("never shows an answer block for a word search (FR-15)", () => {
    render(<SearchResultsCard results={buildSearchResults()} onOpenRecord={vi.fn()} onSeeAll={vi.fn()} />);

    expect(screen.queryByRole("region", { name: "Answer from your records" })).not.toBeInTheDocument();
    expect(screen.queryByText(/No answer this time/)).not.toBeInTheDocument();
  });
});

/** Epic 006, sub-plan 4.3, F-11 (`SearchExpense`, FR-29, FR-30). */
describe("SearchResultsCard with expenses", () => {
  it("draws an Expenses group with the ₹ marker, the day and the amount, and says why a number matched", () => {
    const onOpenRecord = vi.fn();
    const results = buildSearchResults({
      query: "850",
      groups: [
        {
          recordType: "EXPENSE",
          total: 2,
          hits: [
            {
              citation: null,
              record: {
                __typename: "Expense" as const,
                id: "e1",
                amountPaise: "85000",
                description: "Dinner with friends",
                spentOn: "2026-10-01",
              },
            },
            {
              citation: null,
              record: {
                __typename: "Expense" as const,
                id: "e2",
                amountPaise: "85000",
                description: "Gym membership",
                spentOn: "2026-09-01",
              },
            },
          ],
        },
      ],
    });

    render(<SearchResultsCard results={results} onOpenRecord={onOpenRecord} onSeeAll={vi.fn()} />);

    expect(screen.getByText("Expenses")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Expense" })).toBeInTheDocument();
    expect(screen.getByText("Thu 1 Oct")).toBeInTheDocument();
    expect(screen.getAllByLabelText("850 rupees")).toHaveLength(2);
    expect(screen.getByText("A number also matches expenses of exactly that amount")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Gym membership"));
    expect(onOpenRecord).toHaveBeenCalledWith(expect.objectContaining({ __typename: "Expense", id: "e2" }), {
      kind: "SEARCH_RESULT_OPENED",
      position: 2,
    });
  });

  it("keeps the usual footer for a word search", () => {
    render(<SearchResultsCard results={buildSearchResults()} onOpenRecord={vi.fn()} onSeeAll={vi.fn()} />);

    expect(screen.getByText("Best match first · only your records are searched")).toBeInTheDocument();
  });
});

/** Epic 007, sub-plan 4.2, F-5 (FR-30): the search card's Events group. */
describe("SearchResultsCard with events", () => {
  it("draws an Events group with the diamond, the when and the status, and opens the event", () => {
    const onOpenRecord = vi.fn();
    const results = buildSearchResults({
      query: "dentist",
      groups: [
        {
          recordType: "EVENT",
          total: 1,
          hits: [
            {
              citation: null,
              record: { __typename: "Event" as const, ...buildEvent({ id: "ev1", title: "Dentist" }) },
            },
          ],
        },
      ],
    });

    render(<SearchResultsCard results={results} onOpenRecord={onOpenRecord} onSeeAll={vi.fn()} />);

    expect(screen.getByText("Events")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Event" })).toBeInTheDocument();
    expect(screen.getByText("Mon 12 Oct, all day")).toBeInTheDocument();
    expect(screen.getByText("Upcoming")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Dentist"));
    expect(onOpenRecord).toHaveBeenCalledWith(expect.objectContaining({ __typename: "Event", id: "ev1" }), {
      kind: "SEARCH_RESULT_OPENED",
      position: 1,
    });
  });
});
