import { makeAutoObservable } from "mobx";

import type { MemoryCategory } from "../../types.generated";
import type { MemoryFieldsFragment } from "../fragments/MemoryFields.generated";

/** FR-16's chips: every memory, one category, or the uncategorised ones. */
export type MemoryCategoryFilterType = "ALL" | MemoryCategory | "UNCATEGORISED";

/**
 * The one copy of every memory the client holds (tech stack §3). The Memories
 * tab reads `order`; the All tab, capture's saved card and the detail page
 * read by id, so an edit shows everywhere at once.
 */
export class MemoriesStoreModel {
  memories: Map<string, MemoryFieldsFragment> = new Map();
  order: string[] = [];
  categoryFilter: MemoryCategoryFilterType = "ALL";
  /** When the tab last loaded from the server; null until the first load. */
  lastSyncedAt: Date | null = null;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  get(id: string): MemoryFieldsFragment | null {
    return this.memories.get(id) ?? null;
  }

  getVisible(): MemoryFieldsFragment[] {
    return this.order
      .map((id) => this.memories.get(id))
      .filter((memory): memory is MemoryFieldsFragment => memory !== undefined);
  }

  setMemories(memories: MemoryFieldsFragment[]): void {
    this.order = memories.map((memory) => memory.id);
    for (const memory of memories) {
      this.memories.set(memory.id, memory);
    }
    this.lastSyncedAt = new Date();
  }

  /** Stores a memory without changing the tab's order; the next load places it. */
  upsert(memory: MemoryFieldsFragment): void {
    this.memories.set(memory.id, memory);
  }

  remove(id: string): void {
    this.memories.delete(id);
    this.order = this.order.filter((memoryId) => memoryId !== id);
  }

  setCategoryFilter(filter: MemoryCategoryFilterType): void {
    this.categoryFilter = filter;
  }

  clear(): void {
    this.memories.clear();
    this.order = [];
    this.categoryFilter = "ALL";
    this.lastSyncedAt = null;
  }

  static create(): MemoriesStoreModel {
    return new MemoriesStoreModel();
  }
}
