import { describe, expect, it } from "vitest";

import { buildEvent } from "../testing/eventFixture";
import { EventsStoreModel } from "./EventsStore";

describe("EventsStore", () => {
  it("lists upcoming soonest first, happening now included, past left out", () => {
    const store = EventsStoreModel.create();
    store.setAll([
      buildEvent({ id: "late", startsAt: "2026-12-20T00:00:00Z" }),
      buildEvent({ id: "now", startsAt: "2026-10-02T08:30:00Z", eventStatus: "HAPPENING_NOW" }),
      buildEvent({ id: "old", startsAt: "2026-09-26T13:30:00Z", eventStatus: "PAST" }),
      buildEvent({ id: "soon", startsAt: "2026-10-09T10:30:00Z" }),
    ]);

    expect(store.upcoming.map((event) => event.id)).toEqual(["now", "soon", "late"]);
  });

  it("lists past most recent first", () => {
    const store = EventsStoreModel.create();
    store.setAll([
      buildEvent({ id: "2019", startsAt: "2019-06-13T18:30:00Z", eventStatus: "PAST" }),
      buildEvent({ id: "sep", startsAt: "2026-09-26T13:30:00Z", eventStatus: "PAST" }),
    ]);

    expect(store.past.map((event) => event.id)).toEqual(["sep", "2019"]);
  });

  it("setAll replaces what was held; upsert keeps it", () => {
    const store = EventsStoreModel.create();
    store.upsert(buildEvent({ id: "a" }));
    store.setAll([buildEvent({ id: "b" })]);
    store.upsert(buildEvent({ id: "c" }));

    expect(store.get("a")).toBeNull();
    expect(store.totalCount).toBe(2);
    expect(store.lastSyncedAt).not.toBeNull();
  });

  it("an upsert moves an event between groups by its status", () => {
    const store = EventsStoreModel.create();
    store.setAll([buildEvent({ id: "a" })]);
    store.upsert(buildEvent({ id: "a", eventStatus: "PAST" }));

    expect(store.upcoming).toHaveLength(0);
    expect(store.past.map((event) => event.id)).toEqual(["a"]);
  });

  it("clear forgets every event and the sync time", () => {
    const store = EventsStoreModel.create();
    store.setAll([buildEvent()]);
    store.clear();

    expect(store.totalCount).toBe(0);
    expect(store.lastSyncedAt).toBeNull();
  });
});
