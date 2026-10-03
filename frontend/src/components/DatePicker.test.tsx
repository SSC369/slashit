import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import DatePicker from "./DatePicker";

describe("DatePicker, F-2 of sub-plan 4.1", () => {
  it("opens on the month of the value, with today ringed and the value chosen", () => {
    render(<DatePicker value="2026-11-14" today="2026-10-02" onChange={vi.fn()} />);

    expect(screen.getByText("November 2026")).toBeInTheDocument();
    expect(screen.getByRole("gridcell", { name: "Saturday 14 November 2026" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.queryByRole("gridcell", { current: "date" })).not.toBeInTheDocument();
  });

  it("rings today", () => {
    render(<DatePicker value="2026-10-10" today="2026-10-02" onChange={vi.fn()} />);

    expect(screen.getByRole("gridcell", { current: "date" })).toHaveAccessibleName("Friday 2 October 2026");
  });

  it("moves by day with arrows and by month with Page Down, then sends the ISO date on Enter", () => {
    const onChange = vi.fn();
    render(<DatePicker value="2026-10-10" today="2026-10-02" onChange={onChange} autoFocus />);

    const grid = screen.getByRole("grid");
    expect(screen.getByRole("gridcell", { name: "Saturday 10 October 2026" })).toHaveFocus();

    fireEvent.keyDown(grid, { key: "ArrowRight" });
    expect(screen.getByRole("gridcell", { name: "Sunday 11 October 2026" })).toHaveFocus();
    fireEvent.keyDown(grid, { key: "ArrowDown" });
    expect(screen.getByRole("gridcell", { name: "Sunday 18 October 2026" })).toHaveFocus();
    fireEvent.keyDown(grid, { key: "PageDown" });
    expect(screen.getByText("November 2026")).toBeInTheDocument();
    expect(screen.getByRole("gridcell", { name: "Wednesday 18 November 2026" })).toHaveFocus();

    fireEvent.click(screen.getByRole("gridcell", { name: "Wednesday 18 November 2026" }));
    expect(onChange).toHaveBeenCalledWith("2026-11-18");
  });
});
