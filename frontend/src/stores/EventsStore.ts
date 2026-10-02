import { makeAutoObservable } from "mobx";

import type { EventFieldsFragment } from "../fragments/EventFields.generated";

const bySoonest = (left: EventFieldsFragment, right: EventFieldsFragment): number =>
  left.startsAt.localeCompare(right.startsAt);

/**
 * The one copy of every event the client holds. `/events`, the Events tab,
 * the All tab and the detail page all read it by id, so a change shows
 * everywhere at once. The orderings are computed, not stored: an event moves
 * from upcoming to past on its own status, with no list to keep in step.
 */
export class EventsStoreModel {
  events: Map<string, EventFieldsFragment> = new Map();
  /** When every event last came from the server; the Events tab's offline
   * state and its loading state read it. */
  lastSyncedAt: Date | null = null;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get(id: string): EventFieldsFragment | null {
    return this.events.get(id) ?? null;
  }

  /** FR-24: not yet ended, soonest first. "Happening now" counts. */
  get upcoming(): EventFieldsFragment[] {
    return [...this.events.values()].filter((event) => event.eventStatus !== "PAST").sort(bySoonest);
  }

  /** FR-25: past events, most recent first. */
  get past(): EventFieldsFragment[] {
    return [...this.events.values()]
      .filter((event) => event.eventStatus === "PAST")
      .sort((left, right) => bySoonest(right, left));
  }

  get totalCount(): number {
    return this.events.size;
  }

  /** Every event, from the Events tab's load. Replaces what was held. */
  setAll(events: EventFieldsFragment[]): void {
    this.events = new Map(events.map((event) => [event.id, event]));
    this.lastSyncedAt = new Date();
  }

  upsert(event: EventFieldsFragment): void {
    this.events.set(event.id, event);
  }

  remove(id: string): void {
    this.events.delete(id);
  }

  clear(): void {
    this.events.clear();
    this.lastSyncedAt = null;
  }

  static create(): EventsStoreModel {
    return new EventsStoreModel();
  }
}
