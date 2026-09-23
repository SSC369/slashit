import { makeAutoObservable } from "mobx";

export class SettingsStoreModel {
  timezone: string | null = null;
  /** "HH:MM". The snooze menu's "Tomorrow" reads it (FR-21). */
  defaultReminderTime: string | null = null;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  setSettings(settings: { timezone: string; defaultReminderTime?: string }): void {
    this.timezone = settings.timezone;
    if (settings.defaultReminderTime !== undefined) {
      this.defaultReminderTime = settings.defaultReminderTime;
    }
  }

  clear(): void {
    this.timezone = null;
    this.defaultReminderTime = null;
  }

  static create(): SettingsStoreModel {
    return new SettingsStoreModel();
  }
}
