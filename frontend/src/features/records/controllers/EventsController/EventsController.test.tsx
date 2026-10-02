import { CombinedGraphQLErrors } from "@apollo/client/errors";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { API_FAILED, API_FETCHING, API_SUCCESS } from "../../../../constants/apiConstants";
import type { EventFieldsFragment } from "../../../../fragments/EventFields.generated";
import { RootStore } from "../../../../stores/RootStore";
import { StoreProvider } from "../../../../stores/StoreProvider";
import { buildEvent } from "../../../../testing/eventFixture";
import EventsController from "./EventsController";

const { mockUseGetEvents, mockUseOnlineStatus } = vi.hoisted(() => ({
  mockUseGetEvents: vi.fn(),
  mockUseOnlineStatus: vi.fn(() => true),
}));

vi.mock("../../../../api/queries/GetEvents/useGetEvents", () => ({
  default: () => mockUseGetEvents(),
}));
vi.mock("../../../../hooks/useOnlineStatus", () => ({
  useOnlineStatus: () => mockUseOnlineStatus(),
}));

const renderTab = (store: RootStore = new RootStore()): RootStore => {
  render(
    <MemoryRouter initialEntries={["/records"]}>
      <StoreProvider store={store}>
        <Routes>
          <Route path="/records" element={<EventsController />} />
          <Route path="/records/events/:id" element={<div>Event page</div>} />
        </Routes>
      </StoreProvider>
    </MemoryRouter>,
  );
  return store;
};

const withEvents = (events: EventFieldsFragment[]) => ({
  triggerAPI: vi.fn(),
  data: { events },
  apiStatus: API_SUCCESS,
  apiError: null,
});

describe("EventsController, T-1.11 of sub-plan 4.1", () => {
  afterEach(() => {
    vi.clearAllMocks();
    mockUseOnlineStatus.mockReturnValue(true);
  });

  it("asks for every event, past included", () => {
    const triggerAPI = vi.fn();
    mockUseGetEvents.mockReturnValue({ triggerAPI, data: undefined, apiStatus: API_FETCHING, apiError: null });

    renderTab();

    expect(triggerAPI).toHaveBeenCalledWith({ scope: "ALL" });
    expect(screen.getByText("Upcoming")).toBeInTheDocument();
  });

  it("lists upcoming first, then past most recent first (RecordsEvents, FR-25)", () => {
    mockUseGetEvents.mockReturnValue(
      withEvents([
        buildEvent({ id: "u", title: "Dentist", startsAt: "2026-10-09T10:30:00Z", location: "Apollo Clinic" }),
        buildEvent({ id: "p1", title: "Graduation", startsAt: "2019-06-13T18:30:00Z", eventStatus: "PAST" }),
        buildEvent({ id: "p2", title: "Housewarming", startsAt: "2026-09-26T13:30:00Z", eventStatus: "PAST" }),
      ]),
    );

    renderTab();

    const titles = screen.getAllByRole("row").map((row) => row.textContent ?? "");
    const order = ["Dentist", "Housewarming", "Graduation"].map((title) =>
      titles.findIndex((text) => text.includes(title)),
    );
    expect(order).toEqual([...order].sort((left, right) => left - right));
    expect(screen.getByText("Apollo Clinic")).toBeInTheDocument();
    expect(screen.getByText("3 events")).toBeInTheDocument();
    expect(screen.getAllByText("Past").length).toBeGreaterThanOrEqual(2);
  });

  it("marks an event with an alert by its bell (design §7)", () => {
    mockUseGetEvents.mockReturnValue(withEvents([buildEvent()]));

    renderTab();

    expect(screen.getByRole("img", { name: "alert set, 1 day before" })).toBeInTheDocument();
  });

  it("opens an event's detail", () => {
    mockUseGetEvents.mockReturnValue(withEvents([buildEvent({ id: "e1" })]));

    renderTab();
    fireEvent.click(screen.getByText("Mom's birthday"));

    expect(screen.getByText("Event page")).toBeInTheDocument();
  });

  it("draws the empty state", () => {
    mockUseGetEvents.mockReturnValue(withEvents([]));

    renderTab();

    expect(screen.getByText("No events yet")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Go to Capture" })).toBeInTheDocument();
  });

  it("draws the error state with Try again", () => {
    const triggerAPI = vi.fn();
    mockUseGetEvents.mockReturnValue({
      triggerAPI,
      data: undefined,
      apiStatus: API_FAILED,
      apiError: new Error("Failed to fetch"),
    });

    renderTab();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(screen.getByText("Couldn't load your events")).toBeInTheDocument();
    expect(triggerAPI).toHaveBeenCalledTimes(2);
  });

  it("draws the signed-out state when the session has ended", () => {
    mockUseGetEvents.mockReturnValue({
      triggerAPI: vi.fn(),
      data: undefined,
      apiStatus: API_FAILED,
      apiError: new CombinedGraphQLErrors({ errors: [{ message: "Not authenticated" }] }),
    });

    renderTab();

    expect(screen.getByText("Your session ended")).toBeInTheDocument();
  });

  it("keeps loaded rows readable offline, under the offline note", () => {
    const store = new RootStore();
    store.events.setAll([buildEvent()]);
    mockUseOnlineStatus.mockReturnValue(false);
    mockUseGetEvents.mockReturnValue({
      triggerAPI: vi.fn(),
      data: undefined,
      apiStatus: API_FAILED,
      apiError: new Error("Failed to fetch"),
    });

    renderTab(store);

    expect(screen.getByText("You are offline.")).toBeInTheDocument();
    expect(screen.getByText("Mom's birthday")).toBeInTheDocument();
  });
});
