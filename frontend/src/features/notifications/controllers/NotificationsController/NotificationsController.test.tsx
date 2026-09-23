import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import PageTopbar from "../../../../components/PageTopbar";
import { API_FAILED, API_INITIAL, API_SUCCESS } from "../../../../constants/apiConstants";
import type { NotificationFieldsFragment } from "../../../../fragments/NotificationFields.generated";
import { RootStore } from "../../../../stores/RootStore";
import { StoreProvider } from "../../../../stores/StoreProvider";
import NotificationsController from "./NotificationsController";

const mocks = vi.hoisted(() => ({
  getNotifications: vi.fn(),
  listResult: { data: undefined as unknown, apiStatus: 0 as number },
  countResult: { data: undefined as unknown },
  markDone: vi.fn(),
  snooze: vi.fn(),
  markRead: vi.fn(),
  markAllRead: vi.fn(),
  onlineStatus: vi.fn(),
  subscription: { onNotificationReceived: undefined as undefined | ((item: unknown) => void) },
}));

vi.mock("../../../../api/queries/GetNotifications/useGetNotifications", () => ({
  default: () => ({
    triggerAPI: mocks.getNotifications,
    data: mocks.listResult.data,
    apiStatus: mocks.listResult.apiStatus,
    apiError: null,
  }),
}));
vi.mock("../../../../api/queries/GetUnreadNotificationCount/useGetUnreadNotificationCount", () => ({
  default: () => ({ triggerAPI: vi.fn(), data: mocks.countResult.data, apiStatus: 0, apiError: null }),
}));
vi.mock("../../../../api/queries/GetSettings/useGetSettings", () => ({
  default: () => ({
    triggerAPI: vi.fn(),
    data: { settings: { timezone: "Asia/Kolkata", updatedAt: "", defaultReminderTime: "09:00" } },
    apiStatus: 200,
    apiError: null,
  }),
}));
vi.mock("../../../../api/mutations/MarkReminderDone/useMarkReminderDone", () => ({
  default: () => ({ triggerAPI: mocks.markDone, apiStatus: 0, apiError: null }),
}));
vi.mock("../../../../api/mutations/SnoozeReminder/useSnoozeReminder", () => ({
  default: () => ({ triggerAPI: mocks.snooze, apiStatus: 0, apiError: null }),
}));
vi.mock("../../../../api/mutations/MarkNotificationRead/useMarkNotificationRead", () => ({
  default: () => ({ triggerAPI: mocks.markRead, apiStatus: 0, apiError: null }),
}));
vi.mock("../../../../api/mutations/MarkAllNotificationsRead/useMarkAllNotificationsRead", () => ({
  default: () => ({ triggerAPI: mocks.markAllRead, apiStatus: 0, apiError: null }),
}));
vi.mock("../../../../api/subscriptions/NotificationReceived/useNotificationReceived", () => ({
  default: (args: { onNotificationReceived: (item: unknown) => void }) => {
    mocks.subscription.onNotificationReceived = args.onNotificationReceived;
  },
}));
vi.mock("../../../../hooks/useOnlineStatus", () => ({
  useOnlineStatus: () => mocks.onlineStatus(),
}));

const notification = (overrides: Partial<NotificationFieldsFragment> = {}): NotificationFieldsFragment => ({
  id: "n1",
  kind: "REMINDER",
  targetId: "r1",
  title: "Call Mom",
  detail: "",
  marker: "NONE",
  occurredAt: "2026-09-24T13:30:00Z",
  createdAt: "2026-09-24T13:30:02Z",
  read: false,
  action: null,
  actedAt: null,
  showPopup: true,
  ...overrides,
});

const renderShell = (store: RootStore = new RootStore()): RootStore => {
  render(
    <MemoryRouter>
      <StoreProvider store={store}>
        <PageTopbar title="Capture" />
        <NotificationsController />
      </StoreProvider>
    </MemoryRouter>,
  );
  return store;
};

const push = (item: NotificationFieldsFragment): void => {
  act(() => mocks.subscription.onNotificationReceived?.(item));
};

describe("NotificationsController", () => {
  beforeEach(() => {
    mocks.onlineStatus.mockReturnValue(true);
    mocks.listResult.data = undefined;
    mocks.listResult.apiStatus = API_INITIAL;
    mocks.countResult.data = { unreadNotificationCount: 2 };
  });

  afterEach(() => {
    vi.clearAllMocks();
    document.title = "Slashit";
  });

  it("TC-2.16: the bell shows the count and the tab title carries it", () => {
    renderShell();

    expect(screen.getByRole("button", { name: "Notifications, 2 unread" })).toBeInTheDocument();
    expect(document.title).toBe("(2) Slashit");
  });

  it("TC-2.16: the panel loads on first open, with skeletons until it arrives", () => {
    renderShell();

    fireEvent.click(screen.getByRole("button", { name: /Notifications, 2 unread/ }));

    expect(mocks.getNotifications).toHaveBeenCalledWith({ cursor: null });
    expect(screen.getByRole("complementary", { name: "Notifications" })).toBeInTheDocument();
    expect(screen.queryByText("Nothing here yet")).not.toBeInTheDocument();
  });

  it("TC-2.16: the panel's error and empty states", () => {
    mocks.listResult.apiStatus = API_FAILED;
    const store = renderShell();
    act(() => store.notifications.setPanelOpen(true));
    expect(screen.getByText("Couldn't load notifications")).toBeInTheDocument();

    act(() => store.notifications.setPage([], null));
    expect(screen.getByText("Nothing here yet")).toBeInTheDocument();
  });

  it("TC-2.17: a push adds the item, counts it, and pops up once", () => {
    mocks.listResult.apiStatus = API_SUCCESS;
    const store = renderShell();

    push(notification());
    push(notification());

    expect(store.notifications.unreadCount).toBe(3);
    expect(screen.getAllByRole("button", { name: "Close reminder" })).toHaveLength(1);
    expect(screen.getByRole("status", { name: "" })).toHaveTextContent(/Reminder: Call Mom/);
  });

  it("TC-2.17: with pop-ups off, the push is listed but does not pop up", () => {
    const store = renderShell();

    push(notification({ showPopup: false }));

    expect(store.notifications.order).toEqual(["n1"]);
    expect(screen.queryByRole("button", { name: "Close reminder" })).not.toBeInTheDocument();
  });

  it("TC-2.18: Done shows a spinner, then the card leaves", () => {
    let finishDone: () => void = () => undefined;
    mocks.markDone.mockImplementation((args) => {
      finishDone = () => args.onReminderActed({ id: "r1", state: "DONE" });
    });
    const store = renderShell();
    push(notification());

    fireEvent.click(screen.getByRole("button", { name: /Done/ }));
    expect(screen.getByRole("button", { name: "Marking done" })).toHaveAttribute("aria-busy", "true");

    act(() => finishDone());
    expect(screen.queryByRole("button", { name: "Close reminder" })).not.toBeInTheDocument();
    expect(store.notifications.items.get("n1")?.action).toBe("DONE");
  });

  it("TC-2.18: a failed Done keeps the card and says so", () => {
    mocks.markDone.mockImplementation((args) => args.onRequestFailed(new Error("network")));
    renderShell();
    push(notification());

    fireEvent.click(screen.getByRole("button", { name: /Done/ }));

    expect(screen.getByRole("alert")).toHaveTextContent(
      "That didn't save. The reminder is still open. Try again.",
    );
    expect(screen.getByRole("button", { name: "Close reminder" })).toBeInTheDocument();
  });

  it("TC-2.18: offline, Done and Snooze are disabled and Open still works", () => {
    mocks.onlineStatus.mockReturnValue(false);
    renderShell();
    push(notification());

    expect(screen.getByText("You're offline. Done and Snooze need a connection.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Done/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Snooze/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: /Open/ })).toBeEnabled();
  });

  it("TC-2.18: the Snooze menu shows the time each choice lands on", () => {
    renderShell();
    push(notification());

    fireEvent.click(screen.getByRole("button", { name: /Snooze/ }));
    fireEvent.click(screen.getByRole("menuitem", { name: /Tomorrow/ }));

    expect(mocks.snooze).toHaveBeenCalledWith(
      expect.objectContaining({ id: "r1", option: "TOMORROW" }),
    );
  });

  it("the Snooze menu lists all three choices with their times", () => {
    renderShell();
    push(notification());

    fireEvent.click(screen.getByRole("button", { name: /Snooze/ }));

    expect(screen.getByRole("menuitem", { name: /10 minutes/ })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /1 hour/ })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: "Tomorrow, 9:00 AM" })).toBeInTheDocument();
  });
});
