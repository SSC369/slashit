import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { API_FAILED, API_SUCCESS } from "@/constants/apiConstants";
import { RootStore } from "@/stores/RootStore";
import { StoreProvider } from "@/stores/StoreProvider";
import { buildMemory } from "@/testing/memoryFixture";
import { buildReminder } from "@/testing/reminderFixture";
import { buildTask } from "@/testing/searchFixture";
import RelatedRecordsController from "../controllers/RelatedRecordsController/RelatedRecordsController";

const { mockRelated, mockTriggerRelated, mockRecordSearchEvent } = vi.hoisted(() => ({
  mockRelated: { current: { data: undefined as unknown, apiStatus: 0 } },
  mockTriggerRelated: vi.fn(),
  mockRecordSearchEvent: vi.fn(),
}));

vi.mock("@/api/queries/GetRelatedRecords/useGetRelatedRecords", () => ({
  default: () => ({
    triggerAPI: mockTriggerRelated,
    data: mockRelated.current.data,
    apiStatus: mockRelated.current.apiStatus,
    apiError: null,
  }),
}));

vi.mock("@/api/mutations/RecordSearchEvent/useRecordSearchEvent", () => ({
  default: () => ({ triggerAPI: mockRecordSearchEvent, apiStatus: 0, apiError: null }),
}));

const renderRelated = () =>
  render(
    <MemoryRouter>
      <StoreProvider store={new RootStore()}>
        <RelatedRecordsController recordType="TASK" id="t1" />
      </StoreProvider>
    </MemoryRouter>,
  );

/** Epic 005, sub-plan 4.3, C-3.11 (FR-25 to FR-28). */
describe("Related records", () => {
  afterEach(() => {
    mockRelated.current = { data: undefined, apiStatus: 0 };
    vi.clearAllMocks();
  });

  it("lists records of any type, each with its type, title, date and status", () => {
    mockRelated.current = {
      apiStatus: API_SUCCESS,
      data: {
        relatedRecords: [
          { __typename: "Memory", ...buildMemory({ id: "m1", text: "My passport expires in 2030", category: "LIFE" }) },
          { __typename: "Reminder", ...buildReminder({ id: "r1", description: "Check passport renewal requirements" }) },
          { __typename: "Task", ...buildTask({ id: "t2", title: "Book visa appointment" }) },
        ],
      },
    };
    renderRelated();

    expect(mockTriggerRelated).toHaveBeenCalledWith({ recordType: "TASK", id: "t1" });
    expect(screen.getByText("Found by meaning · not links you made")).toBeInTheDocument();
    expect(screen.getByText("My passport expires in 2030")).toBeInTheDocument();
    expect(screen.getByText("Life")).toBeInTheDocument();
    expect(screen.getByText("Check passport renewal requirements")).toBeInTheDocument();
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  it("records an opened related record with its place in the list", () => {
    mockRelated.current = {
      apiStatus: API_SUCCESS,
      data: {
        relatedRecords: [
          { __typename: "Memory", ...buildMemory({ id: "m1", text: "My passport expires in 2030" }) },
          { __typename: "Task", ...buildTask({ id: "t2", title: "Book visa appointment" }) },
        ],
      },
    };
    renderRelated();

    fireEvent.click(screen.getByText("Book visa appointment"));

    expect(mockRecordSearchEvent).toHaveBeenCalledWith({ kind: "RELATED_OPENED", position: 2 });
  });

  it("says nothing is related yet (FR-26)", () => {
    mockRelated.current = { apiStatus: API_SUCCESS, data: { relatedRecords: [] } };
    renderRelated();

    expect(screen.getByText("Nothing related yet")).toBeInTheDocument();
    expect(
      screen.getByText("As you record more, records close in meaning to this one appear here."),
    ).toBeInTheDocument();
  });

  it("says in one line that the list failed, and tries again (FR-28)", () => {
    mockRelated.current = { apiStatus: API_FAILED, data: undefined };
    renderRelated();

    expect(screen.getByText("Related records could not be loaded.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(mockTriggerRelated).toHaveBeenCalledTimes(2);
  });

  it("shows skeleton rows while loading", () => {
    renderRelated();

    expect(screen.getByRole("region", { name: "Related records" })).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByText("Nothing related yet")).not.toBeInTheDocument();
  });
});
