import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { API_FAILED, API_FETCHING, API_SUCCESS } from "../../../../constants/apiConstants";
import type { EventFieldsFragment } from "../../../../fragments/EventFields.generated";
import { RootStore } from "../../../../stores/RootStore";
import { StoreProvider } from "../../../../stores/StoreProvider";
import { buildEvent } from "../../../../testing/eventFixture";
import EventDetailController from "./EventDetailController";

const { mockUseGetEvent } = vi.hoisted(() => ({ mockUseGetEvent: vi.fn() }));

vi.mock("../../../../api/queries/GetEvent/useGetEvent", () => ({
  default: () => mockUseGetEvent(),
}));

const loadedAs = (event: EventFieldsFragment | null): void => {
  mockUseGetEvent.mockReturnValue({
    triggerAPI: vi.fn(),
    data:
      event === null
        ? { event: { __typename: "EventNotFound", message: "gone" } }
        : { event: { __typename: "Event", ...event } },
    apiStatus: API_SUCCESS,
    apiError: null,
  });
};

const renderAt = (path: string): RootStore => {
  const store = new RootStore();
  render(
    <MemoryRouter initialEntries={[path]}>
      <StoreProvider store={store}>
        <Routes>
          <Route path="/records/events/:id" element={<EventDetailController />} />
        </Routes>
      </StoreProvider>
    </MemoryRouter>,
  );
  return store;
};

describe("EventDetailController, T-1.11 of sub-plan 4.1", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("shows every field of a yearly event, its next date and alert (EventDetail, FR-27)", () => {
    loadedAs(buildEvent({ id: "e1" }));

    renderAt("/records/events/e1");

    expect(screen.getByText("Next")).toBeInTheDocument();
    expect(screen.getByText("Mon 12 Oct 2026")).toBeInTheDocument();
    expect(screen.getByText("All day · stays on 12 Oct if you change timezone")).toBeInTheDocument();
    expect(screen.getByText("On 12 Oct")).toBeInTheDocument();
    expect(screen.getByText(/Fires Sun 11 Oct, 9:00 AM · then every year/)).toBeInTheDocument();
    expect(screen.getAllByText("None")).toHaveLength(2);
    expect(screen.getByText("Asia/Kolkata")).toBeInTheDocument();
    expect(screen.getByText("/add-event Mom's birthday October 12, remind me 1 day before")).toBeInTheDocument();
    expect(screen.getByText(/Editing changes every year's occurrence/)).toBeInTheDocument();
  });

  it("shows a timed event's end, length, location and description (EventDetailTimed)", () => {
    loadedAs(
      buildEvent({
        id: "e2",
        title: "Dentist",
        allDay: false,
        repeatYearly: false,
        startDate: "2026-10-09",
        occurrenceDate: "2026-10-09",
        occurrenceEndDate: "2026-10-09",
        startTime: "16:00",
        endTime: "17:00",
        startsAt: "2026-10-09T10:30:00Z",
        endsAt: "2026-10-09T11:30:00Z",
        location: "Apollo Clinic, Indiranagar",
        eventDescription: "Bring the old X-rays.",
      }),
    );

    renderAt("/records/events/e2");

    expect(screen.getByText("When")).toBeInTheDocument();
    expect(screen.getByText("Fri 9 Oct 2026, 4:00 to 5:00 PM")).toBeInTheDocument();
    expect(screen.getByText("1 hour")).toBeInTheDocument();
    expect(screen.getByText("Apollo Clinic, Indiranagar")).toBeInTheDocument();
    expect(screen.getByText("Bring the old X-rays.")).toBeInTheDocument();
  });

  it("marks a past event and says where it is still listed (EventDetailPast)", () => {
    loadedAs(buildEvent({ id: "e3", eventStatus: "PAST", repeatYearly: false, alerts: [] }));

    renderAt("/records/events/e3");

    expect(screen.getByText("Past")).toBeInTheDocument();
    expect(screen.getByText(/This event has passed/)).toBeInTheDocument();
  });

  it("draws the not-found state for a missing or foreign id (NFR-6)", () => {
    loadedAs(null);

    renderAt("/records/events/nope");

    expect(screen.getByText("This event doesn't exist or was deleted")).toBeInTheDocument();
  });

  it("draws the skeleton while loading", () => {
    mockUseGetEvent.mockReturnValue({ triggerAPI: vi.fn(), data: undefined, apiStatus: API_FETCHING, apiError: null });

    renderAt("/records/events/e1");

    expect(screen.getByLabelText("Loading event")).toBeInTheDocument();
  });

  it("draws the error state when the load fails with nothing held", () => {
    mockUseGetEvent.mockReturnValue({
      triggerAPI: vi.fn(),
      data: undefined,
      apiStatus: API_FAILED,
      apiError: new Error("Failed to fetch"),
    });

    renderAt("/records/events/e1");

    expect(screen.getByText("Couldn't load this event")).toBeInTheDocument();
  });
});
