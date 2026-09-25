import { makeAutoObservable } from "mobx";

import type { ReminderFieldsFragment } from "../fragments/ReminderFields.generated";

export type ReminderGroupType = "NEEDS_ATTENTION" | "UPCOMING" | "DONE";

interface ReminderGroupsInput {
  needsAttention: ReminderFieldsFragment[];
  upcoming: ReminderFieldsFragment[];
  done: ReminderFieldsFragment[];
}

const groupForState = (state: ReminderFieldsFragment["state"]): ReminderGroupType => {
  if (state === "FIRED") return "NEEDS_ATTENTION";
  if (state === "DONE") return "DONE";
  return "UPCOMING";
};

/**
 * The one copy of every reminder the client holds (index §6). The Reminders
 * tab reads its groups; the All tab and the detail page read `reminders` by
 * id through this store, so an edit shows everywhere at once.
 */
export class RemindersStoreModel {
  reminders: Map<string, ReminderFieldsFragment> = new Map();
  groupOrder: Record<ReminderGroupType, string[]> = {
    NEEDS_ATTENTION: [],
    UPCOMING: [],
    DONE: [],
  };
  /** When the groups last came from the server; the offline footer shows it. */
  lastSyncedAt: Date | null = null;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get(id: string): ReminderFieldsFragment | null {
    return this.reminders.get(id) ?? null;
  }

  getGroup(group: ReminderGroupType): ReminderFieldsFragment[] {
    return this.groupOrder[group]
      .map((id) => this.reminders.get(id))
      .filter((reminder): reminder is ReminderFieldsFragment => reminder !== undefined);
  }

  get totalCount(): number {
    return (
      this.groupOrder.NEEDS_ATTENTION.length +
      this.groupOrder.UPCOMING.length +
      this.groupOrder.DONE.length
    );
  }

  get activeCount(): number {
    return this.groupOrder.NEEDS_ATTENTION.length + this.groupOrder.UPCOMING.length;
  }

  setGroups(groups: ReminderGroupsInput): void {
    this.groupOrder = {
      NEEDS_ATTENTION: groups.needsAttention.map((reminder) => reminder.id),
      UPCOMING: groups.upcoming.map((reminder) => reminder.id),
      DONE: groups.done.map((reminder) => reminder.id),
    };
    for (const reminder of [...groups.needsAttention, ...groups.upcoming, ...groups.done]) {
      this.reminders.set(reminder.id, reminder);
    }
    this.lastSyncedAt = new Date();
  }

  /** Stores the reminder and moves it to the group its state now belongs in.
   * A reminder new to its group goes last; the next load puts it in order. */
  upsert(reminder: ReminderFieldsFragment): void {
    this.reminders.set(reminder.id, reminder);
    const group = groupForState(reminder.state);
    if (this.groupOrder[group].includes(reminder.id)) return;
    this.removeFromGroups(reminder.id);
    this.groupOrder[group].push(reminder.id);
  }

  remove(id: string): void {
    this.reminders.delete(id);
    this.removeFromGroups(id);
  }

  clear(): void {
    this.reminders.clear();
    this.groupOrder = { NEEDS_ATTENTION: [], UPCOMING: [], DONE: [] };
    this.lastSyncedAt = null;
  }

  private removeFromGroups(id: string): void {
    this.groupOrder = {
      NEEDS_ATTENTION: this.groupOrder.NEEDS_ATTENTION.filter((groupId) => groupId !== id),
      UPCOMING: this.groupOrder.UPCOMING.filter((groupId) => groupId !== id),
      DONE: this.groupOrder.DONE.filter((groupId) => groupId !== id),
    };
  }

  static create(): RemindersStoreModel {
    return new RemindersStoreModel();
  }
}
