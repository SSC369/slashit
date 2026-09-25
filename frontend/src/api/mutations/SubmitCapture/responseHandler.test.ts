import { describe, expect, it, vi } from "vitest";

import { buildMemory } from "../../../testing/memoryFixture";
import type { SubmitCaptureMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("SubmitCapture responseHandler, epic 004's members", () => {
  it("hands MemorySaved's memory and caution to onMemorySaved", () => {
    const { handleResponse } = useResponseHandler();
    const onMemorySaved = vi.fn();
    const memory = buildMemory();
    const data: SubmitCaptureMutation = {
      submitCapture: { __typename: "MemorySaved", memory, secretCaution: "CREDENTIAL" },
    };

    handleResponse({ data, onMemorySaved });

    expect(onMemorySaved).toHaveBeenCalledWith({ memory, secretCaution: "CREDENTIAL" });
  });

  it("hands MemoriesListed to onMemoriesListed with its search text", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoriesListed = vi.fn();
    const data: SubmitCaptureMutation = {
      submitCapture: { __typename: "MemoriesListed", memories: [], searchText: "visa" },
    };

    handleResponse({ data, onMemoriesListed });

    expect(onMemoriesListed).toHaveBeenCalledWith({ memories: [], searchText: "visa" });
  });

  it("hands MemoryTooLong to onMemoryTooLong", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryTooLong = vi.fn();
    const data: SubmitCaptureMutation = {
      submitCapture: { __typename: "MemoryTooLong", message: "m", length: 612, limit: 500 },
    };

    handleResponse({ data, onMemoryTooLong });

    expect(onMemoryTooLong).toHaveBeenCalledWith({ message: "m", length: 612, limit: 500 });
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { submitCapture: { __typename: "Unknown" } } as unknown as SubmitCaptureMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled CaptureResult type");
  });
});
