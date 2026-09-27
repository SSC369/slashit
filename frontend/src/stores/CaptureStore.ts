import { makeAutoObservable } from "mobx";

import type { MemoryCategory, SecretKind } from "../../types.generated";
import type { MemoryFieldsFragment } from "../fragments/MemoryFields.generated";
import type { ReminderFieldsFragment } from "../fragments/ReminderFields.generated";
import type { TaskFieldsFragment } from "../fragments/TaskFields.generated";

export type CaptureTurn =
  | { id: string; said: string; status: "loading" }
  | { id: string; said: string; status: "taskCreated"; task: TaskFieldsFragment }
  | { id: string; said: string; status: "taskList"; tasks: TaskFieldsFragment[] }
  | { id: string; said: string; status: "reminderCreated"; reminder: ReminderFieldsFragment }
  | { id: string; said: string; status: "reminderList"; reminders: ReminderFieldsFragment[] }
  | { id: string; said: string; status: "reminderLimit"; limit: number }
  | { id: string; said: string; status: "modelDown" }
  | {
      id: string;
      said: string;
      status: "memorySaved";
      memory: MemoryFieldsFragment;
      secretCaution: SecretKind | null;
      /** Set when the save answered a conflict, for the card's headline. */
      resolution?: "KEEP_NEW" | "BOTH";
      /** How many old memories "Keep the new one" forgot. */
      forgottenCount?: number;
    }
  /** `Main`, FR-10 to FR-13: nothing saved until an answer. */
  | {
      id: string;
      said: string;
      status: "memoryConflict";
      pendingCaptureId: string;
      newText: string;
      category: MemoryCategory | null;
      conflicting: MemoryFieldsFragment[];
      /** "Decide later": the card folds but the question still waits. */
      deferred: boolean;
      error: string | null;
    }
  | { id: string; said: string; status: "memoryDiscarded" }
  | { id: string; said: string; status: "conflictGone" }
  | {
      id: string;
      said: string;
      status: "memoryList";
      memories: MemoryFieldsFragment[];
      searchText: string | null;
    }
  | { id: string; said: string; status: "memoryTooLong"; length: number; limit: number }
  | { id: string; said: string; status: "memoryModelDown" }
  | {
      id: string;
      said: string;
      status: "pending";
      pendingCaptureId: string;
      question: string;
      answerDraft: string;
    }
  | { id: string; said: string; status: "nonCommand"; originalInput: string }
  | {
      id: string;
      said: string;
      status: "unrecognisedCommand";
      attemptedName: string;
      closestMatches: string[];
    }
  | { id: string; said: string; status: "refused"; message: string };

/** The turn with the forgotten memories taken out, or null when nothing of it remains. */
const scrubTurn = (turn: CaptureTurn, isGone: (memoryId: string) => boolean): CaptureTurn | null => {
  switch (turn.status) {
    case "memorySaved":
      return isGone(turn.memory.id) ? null : turn;
    case "memoryList": {
      const memories = turn.memories.filter((memory) => !isGone(memory.id));
      return memories.length === turn.memories.length ? turn : { ...turn, memories };
    }
    case "memoryConflict": {
      const conflicting = turn.conflicting.filter((memory) => !isGone(memory.id));
      return conflicting.length === turn.conflicting.length ? turn : { ...turn, conflicting };
    }
    default:
      return turn;
  }
};

type DistributiveOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never;

type CaptureTurnPatch = DistributiveOmit<CaptureTurn, "id" | "said">;

export class CaptureStoreModel {
  turns: Map<string, CaptureTurn> = new Map();
  order: string[] = [];

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  getAll(): CaptureTurn[] {
    return this.order
      .map((id) => this.turns.get(id))
      .filter((turn): turn is CaptureTurn => turn !== undefined);
  }

  addLoadingTurn(said: string): string {
    const id = crypto.randomUUID();
    this.turns.set(id, { id, said, status: "loading" });
    this.order.push(id);
    return id;
  }

  resolveTurn(id: string, patch: CaptureTurnPatch): void {
    const existing = this.turns.get(id);
    if (!existing) return;
    this.turns.set(id, { id: existing.id, said: existing.said, ...patch } as CaptureTurn);
  }

  setAnswerDraft(id: string, answerDraft: string): void {
    const turn = this.turns.get(id);
    if (!turn || turn.status !== "pending") return;
    this.turns.set(id, { ...turn, answerDraft });
  }

  setConflictDeferred(id: string, deferred: boolean): void {
    const turn = this.turns.get(id);
    if (!turn || turn.status !== "memoryConflict") return;
    this.turns.set(id, { ...turn, deferred });
  }

  setConflictError(id: string, error: string | null): void {
    const turn = this.turns.get(id);
    if (!turn || turn.status !== "memoryConflict") return;
    this.turns.set(id, { ...turn, error });
  }

  /** "1 question waiting": every question still open in the stream (Q2). */
  get waitingCount(): number {
    return this.getAll().filter((turn) => turn.status === "pending" || turn.status === "memoryConflict")
      .length;
  }

  /**
   * FR-23 for the open feed: a turn that saved a forgotten memory leaves the
   * feed entirely (user direction 2026-09-27: no placeholder in chat), and
   * lists drop the forgotten rows.
   */
  scrubForgottenMemories(memoryIds: string[]): void {
    const gone = new Set(memoryIds);
    const isGone = (memoryId: string): boolean => gone.has(memoryId);
    for (const turn of this.getAll()) {
      const scrubbed = scrubTurn(turn, isGone);
      if (scrubbed === null) this.removeTurn(turn.id);
      else if (scrubbed !== turn) this.turns.set(turn.id, scrubbed);
    }
  }

  removeTurn(id: string): void {
    this.turns.delete(id);
    this.order = this.order.filter((turnId) => turnId !== id);
  }

  clear(): void {
    this.turns.clear();
    this.order = [];
  }

  static create(): CaptureStoreModel {
    return new CaptureStoreModel();
  }
}
