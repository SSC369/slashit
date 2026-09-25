import { AuthStoreModel } from "./AuthStore";
import { CaptureStoreModel } from "./CaptureStore";
import { NotificationsStoreModel } from "./NotificationsStore";
import { RecordsStoreModel } from "./RecordsStore";
import { RemindersStoreModel } from "./RemindersStore";
import { SettingsStoreModel } from "./SettingsStore";
import { ToastStoreModel } from "./ToastStore";

export class RootStore {
  auth = AuthStoreModel.create();
  capture = CaptureStoreModel.create();
  notifications = NotificationsStoreModel.create();
  reminders = RemindersStoreModel.create();
  records = RecordsStoreModel.create(this.reminders);
  settings = SettingsStoreModel.create();
  toast = ToastStoreModel.create();

  clear(): void {
    this.auth.clear();
    this.capture.clear();
    this.notifications.clear();
    this.records.clear();
    this.reminders.clear();
    this.settings.clear();
    this.toast.clear();
  }
}
