import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { buildExpenseSummary } from "../../../testing/expenseFixture";
import { ExpenseSummaryCard, PeriodNotUnderstoodNote } from "./ExpenseCards";

describe("Expense summary card, F-6 and F-7 of sub-plan 4.2", () => {
  it("lists categories largest first with a total and a count (FR-23, FR-25)", () => {
    const summary = buildExpenseSummary();
    const onOpenInRecords = vi.fn();
    render(<ExpenseSummaryCard summary={summary} onOpenInRecords={onOpenInRecords} />);

    const rows = within(screen.getByRole("table")).getAllByRole("row");
    expect(rows.map((row) => row.textContent)).toEqual([
      "Food₹12,300",
      "Bills₹8,650",
      "Entertainment₹1,200",
      "Total₹38,450",
    ]);
    expect(screen.getByText("September 2026")).toBeInTheDocument();
    expect(screen.getByText("42 expenses")).toBeInTheDocument();
    expect(screen.getByText("Largest first · only your expenses are counted")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Open in Records/ }));
    expect(onOpenInRecords).toHaveBeenCalledWith(summary);
  });

  it("draws each bar as a share of the largest, hidden from screen readers", () => {
    const { container } = render(
      <ExpenseSummaryCard summary={buildExpenseSummary()} onOpenInRecords={vi.fn()} />,
    );

    const fills = [...container.querySelectorAll("[aria-hidden='true'] > i")] as HTMLElement[];
    expect(fills.map((fill) => fill.style.width)).toEqual(["100%", `${(865000 / 1230000) * 100}%`, `${(120000 / 1230000) * 100}%`]);
  });

  it("names an empty period and its range (FR-26)", () => {
    render(
      <ExpenseSummaryCard
        summary={buildExpenseSummary({
          label: "Last week",
          phrase: "last week",
          start: "2026-09-21",
          end: "2026-09-27",
          count: 0,
          grandTotalPaise: "0",
          totals: [],
        })}
        onOpenInRecords={vi.fn()}
      />,
    );

    expect(screen.getByText("No expenses recorded last week")).toBeInTheDocument();
    expect(screen.getByText(/Mon 21 Sep to Sun 27 Sep\. Record one with/)).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("quotes a period it did not understand and lists the accepted ones (FR-27)", () => {
    render(<PeriodNotUnderstoodNote periodText="since diwali" />);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Slashit did not understand “since diwali”. Try today, this week, last week, this month, last month, a month such as august, or this year.",
    );
  });
});
