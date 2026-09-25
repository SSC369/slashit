import { makeAutoObservable } from "mobx";

import type { SecretKind } from "../../types.generated";
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
    }
  | {
      id: string;
      said: string;
      status: "memoryList";
      memories: MemoryFieldsFragment[];
      searchText: string | null;
    }
  | { id: string; said: string; status: "memoryTooLong"; length: number; limit: number }
  | { id: string; said: string; status: "memoryModelDown" }
  /** `ForgetPick`: several matches, none forgotten until one is picked and confirmed. */
  | {
      id: string;
      said: string;
      status: "forgetPick";
      searchText: string;
      candidates: MemoryFieldsFragment[];
      totalMatches: number;
      selectedId: string | null;
    }
  /** `ForgetConfirm`: names the full text; `error` holds a failed request's message. */
  | {
      id: string;
      said: string;
      status: "forgetConfirm";
      memory: MemoryFieldsFragment;
      error: string | null;
    }
  /** `ForgetAll`: `countChanged` when the server refused a stale count (FR-27). */
  | {
      id: string;
      said: string;
      status: "forgetAll";
      count: number;
      countChanged: boolean;
      error: string | null;
    }
  /** FR-26. An empty `searchText` is a bare `/forget`, which explains itself. */
  | { id: string; said: string; status: "forgetNoMatch"; searchText: string }
  | { id: string; said: string; status: "forgotten"; count: number }
  | { id: string; said: string; status: "forgetGone" }
  | { id: string; said: string; status: "forgetCancelled" }
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

  selectForgetCandidate(id: string, memoryId: string): void {
    const turn = this.turns.get(id);
    if (!turn || turn.status !== "forgetPick") return;
    this.turns.set(id, { ...turn, selectedId: memoryId });
  }

  setForgetError(id: string, error: string | null): void {
    const turn = this.turns.get(id);
    if (!turn || (turn.status !== "forgetConfirm" && turn.status !== "forgetAll")) return;
    this.turns.set(id, { ...turn, error });
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
