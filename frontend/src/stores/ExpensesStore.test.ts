import { describe, expect, it } from "vitest";

import type { ExpensePeriodFragment } from "../api/queries/GetExpensePeriods/responseHandler";
import { ExpensesStoreModel, periodIdOf } from "./ExpensesStore";

const period = (overrides: Partial<ExpensePeriodFragment>): ExpensePeriodFragment => ({
  key: "MONTH",
  label: "August 2026",
  phrase: "in August 2026",
  start: "2026-08-01",
  end: "2026-08-31",
  ...overrides,
});

const PERIODS = [
  period({ key: "THIS_MONTH", label: "October 2026 so far", start: "2026-10-01", end: "2026-10-31" }),
  period({ key: "LAST_MONTH", label: "September 2026", start: "2026-09-01", end: "2026-09-30" }),
  period({}),
  period({ key: "ALL_TIME", label: "All time", start: null, end: null }),
];

describe("ExpensesStore periods, sub-plan 4.2", () => {
  it("opens on this month once the periods load (decision 1A)", () => {
    const store = ExpensesStoreModel.create();

    store.setPeriods(PERIODS);

    expect(store.selectedPeriod?.key).toBe("THIS_MONTH");
  });

  it("keeps a period picked before the list loaded, as Open in Records does (F-10)", () => {
    const store = ExpensesStoreModel.create();
    store.selectPeriod(periodIdOf({ start: "2026-08-01", end: "2026-08-31" }));

    store.setPeriods(PERIODS);

    expect(store.selectedPeriod?.label).toBe("August 2026");
  });

  it("falls back to this month when the picked range is not offered", () => {
    const store = ExpensesStoreModel.create();
    store.selectPeriod(periodIdOf({ start: "2020-01-01", end: "2020-01-31" }));

    store.setPeriods(PERIODS);

    expect(store.selectedPeriod?.key).toBe("THIS_MONTH");
  });

  it("names All time by its open range", () => {
    expect(periodIdOf({ start: null, end: null })).toBe("all|all");
  });
});
