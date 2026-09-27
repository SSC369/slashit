import { describe, expect, it, vi } from "vitest";

import { buildMemory } from "../../../testing/memoryFixture";
import type { UpdateMemoryMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("UpdateMemory responseHandler", () => {
  it("hands the saved memory to onMemoryUpdated", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryUpdated = vi.fn();
    const memory = { __typename: "Memory" as const, ...buildMemory() };

    handleResponse({ data: { updateMemory: memory }, onMemoryUpdated });

    expect(onMemoryUpdated).toHaveBeenCalledWith(memory);
  });

  it("calls onMemoryTooLong with the length and limit", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryTooLong = vi.fn();
    const data: UpdateMemoryMutation = {
      updateMemory: { __typename: "MemoryTooLong", message: "too long", length: 501, limit: 500 },
    };

    handleResponse({ data, onMemoryTooLong });

    expect(onMemoryTooLong).toHaveBeenCalledWith({ message: "too long", length: 501, limit: 500 });
  });

  it("calls onInvalidMemory and onMemoryNotFound for their members", () => {
    const { handleResponse } = useResponseHandler();
    const onInvalidMemory = vi.fn();
    const onMemoryNotFound = vi.fn();

    handleResponse({
      data: { updateMemory: { __typename: "InvalidMemory", message: "needs text" } },
      onInvalidMemory,
    });
    handleResponse({
      data: { updateMemory: { __typename: "MemoryNotFound", message: "gone" } },
      onMemoryNotFound,
    });

    expect(onInvalidMemory).toHaveBeenCalledWith("needs text");
    expect(onMemoryNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { updateMemory: { __typename: "Unknown" } } as unknown as UpdateMemoryMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled UpdateMemoryResult type");
  });
});
