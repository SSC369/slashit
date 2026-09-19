import { describe, expect, it, vi } from "vitest";

import { useResponseHandler } from "./responseHandler";
import type { RecordsViewOpenedMutation } from "./operation.generated";

describe("RecordsViewOpened responseHandler", () => {
  it("calls onLogged when the mutation reports true", () => {
    const { handleResponse } = useResponseHandler();
    const onLogged = vi.fn();

    handleResponse({
      data: { recordsViewOpened: true } as RecordsViewOpenedMutation,
      onLogged,
    });

    expect(onLogged).toHaveBeenCalled();
  });

  it("does nothing when data is absent", () => {
    const { handleResponse } = useResponseHandler();
    expect(() => handleResponse({ data: null })).not.toThrow();
  });
});
