import { AuthStoreModel } from "./AuthStore";
import { CaptureStoreModel } from "./CaptureStore";
import { EventsStoreModel } from "./EventsStore";
import { MemoriesStoreModel } from "./MemoriesStore";
import { NotificationsStoreModel } from "./NotificationsStore";
import { RecordsStoreModel } from "./RecordsStore";
import { RelatedRecordsStoreModel } from "./RelatedRecordsStore";
import { RemindersStoreModel } from "./RemindersStore";
import { SettingsStoreModel } from "./SettingsStore";
import { ToastStoreModel } from "./ToastStore";

export class RootStore {
  auth = AuthStoreModel.create();
  capture = CaptureStoreModel.create();
  notifications = NotificationsStoreModel.create();
  reminders = RemindersStoreModel.create();
  memories = MemoriesStoreModel.create();
  events = EventsStoreModel.create();
  records = RecordsStoreModel.create(this.reminders, this.memories, this.events);
  related = RelatedRecordsStoreModel.create(this.records);
  settings = SettingsStoreModel.create();
  toast = ToastStoreModel.create();

  /** Forget (FR-22, FR-23): the memories leave every list, and the open
   * capture feed drops their turns. */
  forgetMemories(memoryIds: string[]): void {
    this.memories.removeMany(memoryIds);
    this.capture.scrubForgottenMemories(memoryIds);
  }

  clear(): void {
    this.auth.clear();
    this.capture.clear();
    this.notifications.clear();
    this.records.clear();
    this.related.clear();
    this.memories.clear();
    this.reminders.clear();
    this.events.clear();
    this.settings.clear();
    this.toast.clear();
  }
}
