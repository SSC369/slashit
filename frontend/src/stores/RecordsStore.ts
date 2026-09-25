import { makeAutoObservable } from "mobx";

import type { RecordItem } from "../api/queries/GetRecords/responseHandler";
import type { MemoryFieldsFragment } from "../fragments/MemoryFields.generated";
import type { ReminderFieldsFragment } from "../fragments/ReminderFields.generated";
import type { TaskFieldsFragment } from "../fragments/TaskFields.generated";
import type { MemoriesStoreModel } from "./MemoriesStore";
import type { RemindersStoreModel } from "./RemindersStore";

export type RecordsKindFilter = "ALL" | "TASKS" | "REMINDERS" | "MEMORIES";
export type RecordsSortField = "CREATED_AT" | "DUE_AT";

export type RecordRow =
  | { kind: "TASK"; task: TaskFieldsFragment }
  | { kind: "REMINDER"; reminder: ReminderFieldsFragment }
  | { kind: "MEMORY"; memory: MemoryFieldsFragment };

interface RecordRef {
  kind: RecordRow["kind"];
  id: string;
}

export class RecordsStoreModel {
  /** Tasks by id. Reminders and memories live in their own stores, never here. */
  records: Map<string, TaskFieldsFragment> = new Map();
  order: RecordRef[] = [];
  kindFilter: RecordsKindFilter = "ALL";
  searchText = "";
  sortField: RecordsSortField = "CREATED_AT";

  private readonly remindersStore: RemindersStoreModel;
  private readonly memoriesStore: MemoriesStoreModel;

  constructor(remindersStore: RemindersStoreModel, memoriesStore: MemoriesStoreModel) {
    this.remindersStore = remindersStore;
    this.memoriesStore = memoriesStore;
    makeAutoObservable<RecordsStoreModel, "remindersStore" | "memoriesStore">(
      this,
      { remindersStore: false, memoriesStore: false },
      { autoBind: true },
    );
  }

  getVisible(): RecordRow[] {
    // The server already applies kindFilter/searchText/sortField (the
    // controller passes them to the GetRecords query); this just renders
    // whatever the store currently holds, in the order the server returned.
    const rows: RecordRow[] = [];
    for (const ref of this.order) {
      if (ref.kind === "TASK") {
        const task = this.records.get(ref.id);
        if (task !== undefined) rows.push({ kind: "TASK", task });
      } else if (ref.kind === "MEMORY") {
        const memory = this.memoriesStore.get(ref.id);
        if (memory !== null) rows.push({ kind: "MEMORY", memory });
      } else {
        const reminder = this.remindersStore.get(ref.id);
        if (reminder !== null) rows.push({ kind: "REMINDER", reminder });
      }
    }
    return rows;
  }

  setRecords(items: RecordItem[]): void {
    this.records.clear();
    this.order = [];
    for (const item of items) {
      if (item.__typename === "Task") {
        this.records.set(item.id, item);
        this.order.push({ kind: "TASK", id: item.id });
      } else if (item.__typename === "Memory") {
        this.memoriesStore.upsert(item);
        this.order.push({ kind: "MEMORY", id: item.id });
      } else {
        this.remindersStore.upsert(item);
        this.order.push({ kind: "REMINDER", id: item.id });
      }
    }
  }

  upsert(record: TaskFieldsFragment): void {
    if (!this.records.has(record.id)) {
      this.order.push({ kind: "TASK", id: record.id });
    }
    this.records.set(record.id, record);
  }

  remove(id: string): void {
    this.records.delete(id);
    this.order = this.order.filter((ref) => ref.id !== id);
  }

  setKindFilter(filter: RecordsKindFilter): void {
    this.kindFilter = filter;
  }

  setSearchText(text: string): void {
    this.searchText = text;
  }

  setSortField(field: RecordsSortField): void {
    this.sortField = field;
  }

  clear(): void {
    this.records.clear();
    this.order = [];
    this.kindFilter = "ALL";
    this.searchText = "";
    this.sortField = "CREATED_AT";
  }

  static create(
    remindersStore: RemindersStoreModel,
    memoriesStore: MemoriesStoreModel,
  ): RecordsStoreModel {
    return new RecordsStoreModel(remindersStore, memoriesStore);
  }
}
