import { makeAutoObservable } from "mobx";

import type { RecordItem } from "../api/queries/GetRecords/responseHandler";
import type { ReminderFieldsFragment } from "../fragments/ReminderFields.generated";
import type { TaskFieldsFragment } from "../fragments/TaskFields.generated";
import type { RemindersStoreModel } from "./RemindersStore";

export type RecordsKindFilter = "ALL" | "TASKS" | "REMINDERS";
export type RecordsSortField = "CREATED_AT" | "DUE_AT";

export type RecordRow =
  | { kind: "TASK"; task: TaskFieldsFragment }
  | { kind: "REMINDER"; reminder: ReminderFieldsFragment };

interface RecordRef {
  kind: RecordRow["kind"];
  id: string;
}

export class RecordsStoreModel {
  /** Tasks by id. Reminders live in the reminders store, never here. */
  records: Map<string, TaskFieldsFragment> = new Map();
  order: RecordRef[] = [];
  kindFilter: RecordsKindFilter = "ALL";
  searchText = "";
  sortField: RecordsSortField = "CREATED_AT";

  private readonly remindersStore: RemindersStoreModel;

  constructor(remindersStore: RemindersStoreModel) {
    this.remindersStore = remindersStore;
    makeAutoObservable<RecordsStoreModel, "remindersStore">(
      this,
      { remindersStore: false },
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

  static create(remindersStore: RemindersStoreModel): RecordsStoreModel {
    return new RecordsStoreModel(remindersStore);
  }
}
