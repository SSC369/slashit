import { makeAutoObservable } from "mobx";

import type { RecordItem } from "../api/queries/GetRecords/responseHandler";
import type { RecordRef, RecordRow, RecordsStoreModel } from "./RecordsStore";

/**
 * Epic 005, FR-25 to FR-27: each open detail's related list, as references.
 * The records themselves live in their own stores, so an edit or a delete
 * elsewhere shows here at once; nothing is kept beyond this session.
 */
export class RelatedRecordsStoreModel {
  lists: Map<string, RecordRef[]> = new Map();

  private readonly recordsStore: RecordsStoreModel;

  constructor(recordsStore: RecordsStoreModel) {
    this.recordsStore = recordsStore;
    makeAutoObservable<RelatedRecordsStoreModel, "recordsStore">(
      this,
      { recordsStore: false },
      { autoBind: true },
    );
  }

  setRelated(key: string, items: RecordItem[]): void {
    this.lists.set(
      key,
      items.map((item) => this.recordsStore.upsertItem(item)),
    );
  }

  /** Null until the list for `key` has loaded once. */
  getRelated(key: string): RecordRow[] | null {
    const refs = this.lists.get(key);
    return refs === undefined ? null : this.recordsStore.resolveRefs(refs);
  }

  clear(): void {
    this.lists.clear();
  }

  static create(recordsStore: RecordsStoreModel): RelatedRecordsStoreModel {
    return new RelatedRecordsStoreModel(recordsStore);
  }
}
