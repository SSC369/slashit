import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RootStore } from "@/stores/RootStore";
import { StoreProvider } from "@/stores/StoreProvider";
import { buildMemory } from "@/testing/memoryFixture";
import MemoryDetailController from "./MemoryDetailController";

const { mockTriggerForgetMemory, mockForgetApiStatus } = vi.hoisted(() => ({
  mockTriggerForgetMemory: vi.fn(),
  mockForgetApiStatus: { current: 0 },
}));

vi.mock("@/hooks/useOnlineStatus", () => ({ useOnlineStatus: () => true }));

vi.mock("@/api/queries/GetMemory/useGetMemory", () => ({
  default: () => ({ triggerAPI: vi.fn(), data: undefined, apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/mutations/UpdateMemory/useUpdateMemory", () => ({
  default: () => ({ triggerAPI: vi.fn(), apiStatus: 0, apiError: null }),
}));

vi.mock("@/api/mutations/ForgetMemory/useForgetMemory", () => ({
  default: () => ({
    triggerAPI: mockTriggerForgetMemory,
    apiStatus: mockForgetApiStatus.current,
    apiError: null,
  }),
}));

const memory = buildMemory({ id: "m1", text: "My passport expires in 2030" });

const renderDetail = (store: RootStore) =>
  render(
    <MemoryRouter initialEntries={["/records/memories/m1"]}>
      <StoreProvider store={store}>
        <Routes>
          <Route path="/records/memories/:id" element={<MemoryDetailController mode="VIEW" />} />
          <Route path="/records" element={<div>Records page</div>} />
        </Routes>
      </StoreProvider>
    </MemoryRouter>,
  );

describe("MemoryDetailController Forget, F-2.2 of sub-plan 4.2", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("names the full text and the backup line, with focus on Cancel (FR-21, FR-29)", () => {
    const store = new RootStore();
    store.memories.setMemories([memory]);
    renderDetail(store);

    fireEvent.click(screen.getByRole("button", { name: "Forget" }));

    const dialog = screen.getByRole("dialog", { name: "Forget this memory?" });
    expect(dialog).toHaveTextContent("My passport expires in 2030 will be removed for good");
    expect(dialog).toHaveTextContent("Copies in backups are erased on the regular backup schedule.");
    expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
    expect(mockTriggerForgetMemory).not.toHaveBeenCalled();
  });

  it("removes the memory from the tab and goes to Memories with a note", () => {
    mockTriggerForgetMemory.mockImplementation((args) => args.onMemoriesForgotten(1));
    const store = new RootStore();
    store.memories.setMemories([memory]);
    renderDetail(store);

    fireEvent.click(screen.getByRole("button", { name: "Forget" }));
    fireEvent.click(screen.getByRole("button", { name: "Forget memory" }));

    expect(mockTriggerForgetMemory).toHaveBeenCalledWith(expect.objectContaining({ id: "m1" }));
    expect(store.memories.get("m1")).toBeNull();
    expect(store.memories.getVisible()).toHaveLength(0);
    expect(store.records.kindFilter).toBe("MEMORIES");
    expect(store.toast.current?.message).toBe(
      "Memory forgotten. It is gone from your records and your capture history.",
    );
    expect(screen.getByText("Records page")).toBeInTheDocument();
  });

  it("keeps the dialog open with an error when the request fails, and forgets nothing", () => {
    mockTriggerForgetMemory.mockImplementation((args) => args.onRequestFailed(new Error("offline")));
    const store = new RootStore();
    store.memories.setMemories([memory]);
    renderDetail(store);

    fireEvent.click(screen.getByRole("button", { name: "Forget" }));
    fireEvent.click(screen.getByRole("button", { name: "Forget memory" }));

    expect(screen.getByRole("alert")).toHaveTextContent("could not be forgotten");
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
    expect(store.memories.get("m1")).not.toBeNull();
  });
});
