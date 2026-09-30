import { makeAutoObservable } from "mobx";

import type { RecordItem } from "../api/queries/GetRecords/responseHandler";
import type { MemoryFieldsFragment } from "../fragments/MemoryFields.generated";
import type { ReminderFieldsFragment } from "../fragments/ReminderFields.generated";
import type { TaskFieldsFragment } from "../fragments/TaskFields.generated";
import type { MemoriesStoreModel } from "./MemoriesStore";
import type { RemindersStoreModel } from "./RemindersStore";

export type RecordsKindFilter = "ALL" | "TASKS" | "REMINDERS" | "MEMORIES";
export type RecordsSortField = "CREATED_AT" | "DUE_AT";
/** Epic 005, FR-23: a search lists best match first, or the same matches by date. */
export type RecordsSearchSortMode = "BEST_MATCH" | "DATE";

/** One page of the records view's search, as the server ranked it. */
export interface RecordsSearchPage {
  query: string;
  hits: RecordItem[];
  total: number;
  otherTypesTotal: number;
  meaningUnavailable: boolean;
}

export type RecordRow =
  | { kind: "TASK"; task: TaskFieldsFragment }
  | { kind: "REMINDER"; reminder: ReminderFieldsFragment }
  | { kind: "MEMORY"; memory: MemoryFieldsFragment };

const createdAtOf = (row: RecordRow): string => {
  switch (row.kind) {
    case "TASK":
      return row.task.createdAt;
    case "REMINDER":
      return row.reminder.createdAt;
    case "MEMORY":
      return row.memory.createdAt;
  }
};

export interface RecordRef {
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

  // Epic 005, FR-22 to FR-24: the search mode's ranked matches. Separate from
  // `order` so clearing the box returns to the list exactly as it was.
  searchRefs: RecordRef[] = [];
  searchTotal = 0;
  searchOtherTypesTotal = 0;
  searchMeaningUnavailable = false;
  searchSortMode: RecordsSearchSortMode = "BEST_MATCH";
  /** `text|type` of the matches held; null before the first page lands. */
  searchLoadedKey: string | null = null;

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
    return this.resolveRefs(this.order);
  }

  /** Rows for references, skipping any record no longer held (FR-12). */
  resolveRefs(refs: RecordRef[]): RecordRow[] {
    const rows: RecordRow[] = [];
    for (const ref of refs) {
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
    this.order = items.map((item) => this.upsertItem(item));
  }

  /** Puts a record where it lives: tasks here, reminders and memories in
   * their own stores. Returns the reference an ordered list keeps. */
  upsertItem(item: RecordItem): RecordRef {
    if (item.__typename === "Task") {
      this.records.set(item.id, item);
      return { kind: "TASK", id: item.id };
    }
    if (item.__typename === "Memory") {
      this.memoriesStore.upsert(item);
      return { kind: "MEMORY", id: item.id };
    }
    this.remindersStore.upsert(item);
    return { kind: "REMINDER", id: item.id };
  }

  /**
   * Holds one page of matches. The first page replaces what was held; a later
   * one, from Show more, appends. A page whose text is no longer in the box
   * is dropped, so a slow response never overwrites a newer search.
   */
  applySearchPage(args: { key: string; offset: number; page: RecordsSearchPage }): void {
    const { key, offset, page } = args;
    if (page.query !== this.searchText.trim()) return;
    const refs = page.hits.map((item) => this.upsertItem(item));
    if (offset === 0) {
      this.searchRefs = refs;
    } else {
      const held = new Set(this.searchRefs.map((ref) => ref.id));
      this.searchRefs = [...this.searchRefs, ...refs.filter((ref) => !held.has(ref.id))];
    }
    this.searchTotal = page.total;
    this.searchOtherTypesTotal = page.otherTypesTotal;
    this.searchMeaningUnavailable = page.meaningUnavailable;
    this.searchLoadedKey = key;
  }

  /** The held matches, best first, or by created date, newest first (FR-23). */
  getSearchVisible(): RecordRow[] {
    const rows = this.resolveRefs(this.searchRefs);
    if (this.searchSortMode === "BEST_MATCH") return rows;
    return [...rows].sort((left, right) => createdAtOf(right).localeCompare(createdAtOf(left)));
  }

  setSearchSortMode(mode: RecordsSearchSortMode): void {
    this.searchSortMode = mode;
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
    this.searchRefs = this.searchRefs.filter((ref) => ref.id !== id);
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
    this.searchRefs = [];
    this.searchTotal = 0;
    this.searchOtherTypesTotal = 0;
    this.searchMeaningUnavailable = false;
    this.searchSortMode = "BEST_MATCH";
    this.searchLoadedKey = null;
  }

  static create(
    remindersStore: RemindersStoreModel,
    memoriesStore: MemoriesStoreModel,
  ): RecordsStoreModel {
    return new RecordsStoreModel(remindersStore, memoriesStore);
  }
}
