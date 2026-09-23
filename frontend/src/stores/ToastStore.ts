import { makeAutoObservable } from "mobx";

export interface Toast {
  id: string;
  message: string;
  linkLabel: string;
  linkTo: string;
}

/** The success toast (design §4). One at a time: a new one replaces the
 * current one. The component owns the 4-second timer, since hover pauses it. */
export class ToastStoreModel {
  current: Toast | null = null;

  constructor() {
    makeAutoObservable(this, {}, { autoBind: true });
  }

  show(toast: Omit<Toast, "id">): void {
    this.current = { id: crypto.randomUUID(), ...toast };
  }

  dismiss(id: string): void {
    if (this.current?.id === id) this.current = null;
  }

  clear(): void {
    this.current = null;
  }

  static create(): ToastStoreModel {
    return new ToastStoreModel();
  }
}
