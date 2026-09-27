import { describe, expect, it, vi } from "vitest";

import { buildMemory } from "../../../testing/memoryFixture";
import type { ResolveMemoryConflictMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("ResolveMemoryConflict responseHandler, F-3.3 of sub-plan 4.3", () => {
  it("hands the saved memory to onMemorySaved", () => {
    const { handleResponse } = useResponseHandler();
    const onMemorySaved = vi.fn();
    const memory = buildMemory();

    handleResponse({
      data: { resolveMemoryConflict: { __typename: "MemorySaved", memory, secretCaution: null } },
      onMemorySaved,
    });

    expect(onMemorySaved).toHaveBeenCalledWith({ memory, secretCaution: null });
  });

  it("calls onMemoryDiscarded and onPendingCaptureNotFound for their members", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryDiscarded = vi.fn();
    const onPendingCaptureNotFound = vi.fn();

    handleResponse({
      data: { resolveMemoryConflict: { __typename: "MemoryDiscarded", message: "kept" } },
      onMemoryDiscarded,
    });
    handleResponse({
      data: { resolveMemoryConflict: { __typename: "PendingCaptureNotFound", message: "gone" } },
      onPendingCaptureNotFound,
    });

    expect(onMemoryDiscarded).toHaveBeenCalledWith("kept");
    expect(onPendingCaptureNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = {
      resolveMemoryConflict: { __typename: "Unknown" },
    } as unknown as ResolveMemoryConflictMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled ResolveMemoryConflictResult type");
  });
});
