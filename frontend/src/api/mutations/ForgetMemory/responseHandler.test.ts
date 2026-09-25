import { describe, expect, it, vi } from "vitest";

import type { ForgetMemoryMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("ForgetMemory responseHandler", () => {
  it("hands the count to onMemoriesForgotten", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoriesForgotten = vi.fn();

    handleResponse({
      data: { forgetMemory: { __typename: "MemoriesForgotten", count: 1 } },
      onMemoriesForgotten,
    });

    expect(onMemoriesForgotten).toHaveBeenCalledWith(1);
  });

  it("calls onMemoryNotFound with the message", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryNotFound = vi.fn();

    handleResponse({
      data: { forgetMemory: { __typename: "MemoryNotFound", message: "gone" } },
      onMemoryNotFound,
    });

    expect(onMemoryNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { forgetMemory: { __typename: "Unknown" } } as unknown as ForgetMemoryMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled ForgetMemoryResult type");
  });
});
