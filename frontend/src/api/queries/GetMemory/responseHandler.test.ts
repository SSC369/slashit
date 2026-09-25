import { describe, expect, it, vi } from "vitest";

import { buildMemory } from "../../../testing/memoryFixture";
import type { GetMemoryQuery } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("GetMemory responseHandler", () => {
  it("hands a found memory to onMemoryLoaded", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryLoaded = vi.fn();
    const memory = { __typename: "Memory" as const, ...buildMemory() };

    handleResponse({ data: { memory }, onMemoryLoaded });

    expect(onMemoryLoaded).toHaveBeenCalledWith(memory);
  });

  it("calls onMemoryNotFound for MemoryNotFound", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryNotFound = vi.fn();

    handleResponse({ data: { memory: { __typename: "MemoryNotFound", message: "gone" } }, onMemoryNotFound });

    expect(onMemoryNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { memory: { __typename: "Unknown" } } as unknown as GetMemoryQuery;

    expect(() => handleResponse({ data })).toThrow("Unhandled MemoryResult type");
  });
});
