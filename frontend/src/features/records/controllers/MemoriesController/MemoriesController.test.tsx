import { CombinedGraphQLErrors } from "@apollo/client/errors";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { API_FAILED, API_FETCHING, API_SUCCESS } from "../../../../constants/apiConstants";
import { StoreProvider } from "../../../../stores/StoreProvider";
import { buildMemory } from "../../../../testing/memoryFixture";
import MemoriesController from "./MemoriesController";

const { mockUseGetMemories } = vi.hoisted(() => ({ mockUseGetMemories: vi.fn() }));

vi.mock("../../../../api/queries/GetMemories/useGetMemories", () => ({
  default: () => mockUseGetMemories(),
}));

const renderTab = () =>
  render(
    <MemoryRouter>
      <StoreProvider>
        <MemoriesController />
      </StoreProvider>
    </MemoryRouter>,
  );

const withMemories = (memories: ReturnType<typeof buildMemory>[]) => ({
  triggerAPI: vi.fn(),
  data: { memories: memories.map((memory) => ({ __typename: "Memory" as const, ...memory })) },
  apiStatus: API_SUCCESS,
  apiError: null,
});

describe("MemoriesController, F-2 of sub-plan 4.1", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("draws the loading skeleton before the first load", () => {
    mockUseGetMemories.mockReturnValue({ triggerAPI: vi.fn(), data: undefined, apiStatus: API_FETCHING, apiError: null });

    renderTab();

    expect(screen.getByRole("group", { name: "Filter by category" })).toBeInTheDocument();
    expect(screen.queryByText("Only you can see these")).not.toBeInTheDocument();
  });

  it("lists memories with their category and a count (FR-15)", () => {
    mockUseGetMemories.mockReturnValue(
      withMemories([
        buildMemory(),
        buildMemory({ id: "m-2", text: "Netflix renews on the 3rd", category: null }),
      ]),
    );

    renderTab();

    const table = within(screen.getByRole("table"));
    expect(table.getByText("My passport expires in 2030")).toBeInTheDocument();
    expect(table.getByText("Life")).toBeInTheDocument();
    expect(table.getByText("No category")).toBeInTheDocument();
    expect(screen.getByText("2 memories")).toBeInTheDocument();
  });

  it("draws the empty state when nothing has been remembered", () => {
    mockUseGetMemories.mockReturnValue(withMemories([]));

    renderTab();

    expect(screen.getByText("Nothing remembered yet")).toBeInTheDocument();
  });

  it("draws the filtered no-match state and clears back to All (FR-16)", () => {
    mockUseGetMemories.mockReturnValue(withMemories([buildMemory()]));
    renderTab();

    // The server answers the Professional filter with nothing.
    mockUseGetMemories.mockReturnValue(withMemories([]));
    fireEvent.click(screen.getByRole("button", { name: "Professional" }));

    expect(screen.getByText("No memories in Professional")).toBeInTheDocument();
    mockUseGetMemories.mockReturnValue(withMemories([buildMemory()]));
    fireEvent.click(screen.getByRole("button", { name: "Show all" }));
    expect(screen.getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
  });

  it("draws the error state with a retry", () => {
    const triggerAPI = vi.fn();
    mockUseGetMemories.mockReturnValue({
      triggerAPI,
      data: undefined,
      apiStatus: API_FAILED,
      apiError: new Error("network"),
    });

    renderTab();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(screen.getByText("Your memories could not be loaded")).toBeInTheDocument();
    expect(triggerAPI).toHaveBeenCalled();
  });

  it("draws the signed-out state when the session has ended", () => {
    mockUseGetMemories.mockReturnValue({
      triggerAPI: vi.fn(),
      data: undefined,
      apiStatus: API_FAILED,
      apiError: new CombinedGraphQLErrors({ errors: [{ message: "Not authenticated" }] }),
    });

    renderTab();

    expect(screen.getByText("Sign in to see your memories")).toBeInTheDocument();
  });
});
