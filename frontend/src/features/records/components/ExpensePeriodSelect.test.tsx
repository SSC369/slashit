import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ExpensePeriodFragment } from "../../../api/queries/GetExpensePeriods/responseHandler";
import ExpensePeriodSelect from "./ExpensePeriodSelect";

const PERIODS: ExpensePeriodFragment[] = [
  { key: "THIS_MONTH", label: "October 2026 so far", phrase: "this month", start: "2026-10-01", end: "2026-10-31" },
  { key: "MONTH", label: "August 2026", phrase: "in August 2026", start: "2026-08-01", end: "2026-08-31" },
  { key: "ALL_TIME", label: "All time", phrase: "yet", start: null, end: null },
];

describe("ExpensePeriodSelect, F-8 of sub-plan 4.2", () => {
  it("shows the picked period and sends another's range id", () => {
    const onSelect = vi.fn();
    render(<ExpensePeriodSelect periods={PERIODS} selected={PERIODS[0]} onSelect={onSelect} />);

    fireEvent.click(screen.getByRole("button", { name: "Period, October 2026 so far" }));
    expect(screen.getByRole("menuitemradio", { name: "October 2026 so far" })).toHaveAttribute("aria-checked", "true");
    fireEvent.click(screen.getByRole("menuitemradio", { name: "August 2026" }));

    expect(onSelect).toHaveBeenCalledWith("2026-08-01|2026-08-31");
    expect(screen.queryByRole("menuitemradio")).not.toBeInTheDocument();
  });
});
