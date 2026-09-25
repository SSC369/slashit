import { describe, expect, it, vi } from "vitest";

import type { ForgetFromCaptureMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("ForgetFromCapture responseHandler", () => {
  it("hands the count to onMemoriesForgotten", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoriesForgotten = vi.fn();

    handleResponse({
      data: { forgetFromCapture: { __typename: "MemoriesForgotten", count: 2 } },
      onMemoriesForgotten,
    });

    expect(onMemoriesForgotten).toHaveBeenCalledWith(2);
  });

  it("calls onMemoryCountChanged with the new count", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryCountChanged = vi.fn();

    handleResponse({
      data: {
        forgetFromCapture: { __typename: "MemoryCountChanged", message: "changed", count: 24 },
      },
      onMemoryCountChanged,
    });

    expect(onMemoryCountChanged).toHaveBeenCalledWith({ message: "changed", count: 24 });
  });

  it("calls onForgetTargetGone with the message", () => {
    const { handleResponse } = useResponseHandler();
    const onForgetTargetGone = vi.fn();

    handleResponse({
      data: { forgetFromCapture: { __typename: "ForgetTargetGone", message: "already gone" } },
      onForgetTargetGone,
    });

    expect(onForgetTargetGone).toHaveBeenCalledWith("already gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { forgetFromCapture: { __typename: "Unknown" } } as unknown as ForgetFromCaptureMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled ForgetFromCaptureResult type");
  });
});
