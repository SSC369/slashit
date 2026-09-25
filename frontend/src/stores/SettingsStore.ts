import { makeAutoObservable } from "mobx";

export class SettingsStoreModel {
  timezone: string | null = null;
  /** "HH:MM". The snooze menu's "Tomorrow" reads it (FR-21). */
  defaultReminderTime: string | null = null;
  popupsEnabled = true;
  emailEnabled = true;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  setSettings(settings: {
    timezone: string;
    defaultReminderTime?: string;
    popupsEnabled?: boolean;
    emailEnabled?: boolean;
  }): void {
    this.timezone = settings.timezone;
    if (settings.defaultReminderTime !== undefined) {
      this.defaultReminderTime = settings.defaultReminderTime;
    }
    if (settings.popupsEnabled !== undefined) this.popupsEnabled = settings.popupsEnabled;
    if (settings.emailEnabled !== undefined) this.emailEnabled = settings.emailEnabled;
  }

  clear(): void {
    this.timezone = null;
    this.defaultReminderTime = null;
    this.popupsEnabled = true;
    this.emailEnabled = true;
  }

  static create(): SettingsStoreModel {
    return new SettingsStoreModel();
  }
}
