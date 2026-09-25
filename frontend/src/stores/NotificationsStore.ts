import { makeAutoObservable } from "mobx";

import type { NotificationFieldsFragment } from "../fragments/NotificationFields.generated";

export type NotificationActionKindType = "DONE" | "SNOOZE";

export interface NotificationActionState {
  kind: NotificationActionKindType;
  status: "ACTING" | "FAILED";
}

/**
 * The notification list, the bell's count and the open pop-ups (index §6).
 * The list query and the subscription both write through `receive` and
 * `setPage`, so a push and a load never disagree (repo-rules.md §9).
 */
export class NotificationsStoreModel {
  items: Map<string, NotificationFieldsFragment> = new Map();
  order: string[] = [];
  nextCursor: string | null = null;
  hasLoaded = false;
  unreadCount = 0;
  isPanelOpen = false;
  /** Pop-up stack, oldest first; each is a notification id. */
  popupIds: string[] = [];
  /** Done or Snooze in flight or failed, per notification id. */
  actionStates: Map<string, NotificationActionState> = new Map();

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  getAll(): NotificationFieldsFragment[] {
    return this.order
      .map((id) => this.items.get(id))
      .filter((item): item is NotificationFieldsFragment => item !== undefined);
  }

  getPopups(): NotificationFieldsFragment[] {
    return this.popupIds
      .map((id) => this.items.get(id))
      .filter((item): item is NotificationFieldsFragment => item !== undefined);
  }

  setPage(items: NotificationFieldsFragment[], nextCursor: string | null): void {
    this.items.clear();
    this.order = [];
    this.appendPage(items, nextCursor);
    this.hasLoaded = true;
  }

  appendPage(items: NotificationFieldsFragment[], nextCursor: string | null): void {
    for (const item of items) {
      if (!this.items.has(item.id)) this.order.push(item.id);
      this.items.set(item.id, item);
    }
    this.nextCursor = nextCursor;
  }

  /** A push from the subscription: newest first, counted, popped up if the
   * server said so (`showPopup`). A repeat of one already held is ignored. */
  receive(notification: NotificationFieldsFragment): void {
    if (this.items.has(notification.id)) return;
    this.items.set(notification.id, notification);
    this.order.unshift(notification.id);
    if (!notification.read) this.unreadCount += 1;
    if (notification.showPopup && notification.kind === "REMINDER") {
      this.popupIds.push(notification.id);
    }
  }

  setUnreadCount(count: number): void {
    this.unreadCount = count;
  }

  upsert(notification: NotificationFieldsFragment): void {
    const previous = this.items.get(notification.id);
    if (previous !== undefined && !previous.read && notification.read) {
      this.unreadCount = Math.max(this.unreadCount - 1, 0);
    }
    if (previous === undefined) this.order.unshift(notification.id);
    this.items.set(notification.id, notification);
  }

  markAllReadLocally(): void {
    for (const [id, item] of this.items) {
      if (!item.read) this.items.set(id, { ...item, read: true });
    }
    this.unreadCount = 0;
  }

  /** Done or Snooze succeeded on a reminder: every open item for it reads
   * as handled, and its pop-ups close. The server stamped the same. */
  applyReminderAction(reminderId: string, action: "DONE" | "SNOOZED"): void {
    const actedAt = new Date().toISOString();
    for (const [id, item] of this.items) {
      if (item.targetId !== reminderId || item.action !== null) continue;
      if (!item.read) this.unreadCount = Math.max(this.unreadCount - 1, 0);
      this.items.set(id, { ...item, action, actedAt, read: true });
      this.actionStates.delete(id);
    }
    this.popupIds = this.popupIds.filter((id) => this.items.get(id)?.targetId !== reminderId);
  }

  setActionState(id: string, state: NotificationActionState | null): void {
    if (state === null) {
      this.actionStates.delete(id);
      return;
    }
    this.actionStates.set(id, state);
  }

  closePopup(id: string): void {
    this.popupIds = this.popupIds.filter((popupId) => popupId !== id);
  }

  setPanelOpen(isOpen: boolean): void {
    this.isPanelOpen = isOpen;
  }

  clear(): void {
    this.items.clear();
    this.order = [];
    this.nextCursor = null;
    this.hasLoaded = false;
    this.unreadCount = 0;
    this.isPanelOpen = false;
    this.popupIds = [];
    this.actionStates.clear();
  }

  static create(): NotificationsStoreModel {
    return new NotificationsStoreModel();
  }
}
