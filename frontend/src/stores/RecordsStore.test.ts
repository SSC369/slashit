import { describe, expect, it } from "vitest";

import { buildTask } from "../testing/searchFixture";
import type { RecordsSearchPage } from "./RecordsStore";
import { RootStore } from "./RootStore";

const page = (overrides: Partial<RecordsSearchPage> = {}): RecordsSearchPage => ({
  query: "career",
  total: 2,
  otherTypesTotal: 0,
  meaningUnavailable: false,
  hits: [
    { __typename: "Task", ...buildTask({ id: "t1", title: "Career move" }) },
    { __typename: "Task", ...buildTask({ id: "t2", title: "Career fair" }) },
  ],
  ...overrides,
});

/** Epic 005, sub-plan 4.3, C-3.10: the records view's search mode. */
describe("RecordsStore search mode", () => {
  it("drops a page for text no longer in the box", () => {
    const store = new RootStore();
    store.records.setSearchText("career fair");

    store.records.applySearchPage({ key: "career|ALL", offset: 0, page: page() });

    expect(store.records.searchLoadedKey).toBeNull();
    expect(store.records.getSearchVisible()).toEqual([]);
  });

  it("replaces on a first page and appends a later one without repeats", () => {
    const store = new RootStore();
    store.records.setSearchText("career");
    store.records.applySearchPage({ key: "career|ALL", offset: 0, page: page({ total: 3 }) });

    store.records.applySearchPage({
      key: "career|ALL",
      offset: 2,
      page: page({
        total: 3,
        hits: [
          { __typename: "Task", ...buildTask({ id: "t2", title: "Career fair" }) },
          { __typename: "Task", ...buildTask({ id: "t3", title: "Career coach" }) },
        ],
      }),
    });

    expect(store.records.searchRefs.map((ref) => ref.id)).toEqual(["t1", "t2", "t3"]);
    expect(store.records.searchLoadedKey).toBe("career|ALL");
  });

  it("drops a deleted record from the matches, and clearing resets search mode", () => {
    const store = new RootStore();
    store.records.setSearchText("career");
    store.records.applySearchPage({ key: "career|ALL", offset: 0, page: page() });

    store.records.remove("t1");
    expect(store.records.searchRefs.map((ref) => ref.id)).toEqual(["t2"]);

    store.records.setSearchSortMode("DATE");
    store.records.clear();
    expect(store.records.searchRefs).toEqual([]);
    expect(store.records.searchSortMode).toBe("BEST_MATCH");
    expect(store.records.searchLoadedKey).toBeNull();
  });
});
