import { describe, expect, it, vi } from "vitest";

import { useResponseHandler } from "./responseHandler";
import type { RecordSearchEventMutation } from "./operation.generated";

describe("RecordSearchEvent responseHandler", () => {
  it("calls onLogged when the mutation reports true", () => {
    const { handleResponse } = useResponseHandler();
    const onLogged = vi.fn();

    handleResponse({
      data: { recordSearchEvent: true } as RecordSearchEventMutation,
      onLogged,
    });

    expect(onLogged).toHaveBeenCalled();
  });

  it("does nothing when data is absent", () => {
    const { handleResponse } = useResponseHandler();
    const onLogged = vi.fn();
    expect(() => handleResponse({ data: null, onLogged })).not.toThrow();
    expect(onLogged).not.toHaveBeenCalled();
  });
});
