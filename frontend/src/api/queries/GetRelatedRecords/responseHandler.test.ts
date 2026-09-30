import { describe, expect, it, vi } from "vitest";

import { buildTask } from "@/testing/searchFixture";
import { useResponseHandler } from "./responseHandler";
import type { GetRelatedRecordsQuery } from "./operation.generated";

describe("GetRelatedRecords responseHandler", () => {
  it("hands the list, empty or not, to onRelatedLoaded", () => {
    const { handleResponse } = useResponseHandler();
    const onRelatedLoaded = vi.fn();
    const task = { __typename: "Task", ...buildTask() };

    handleResponse({ data: { relatedRecords: [task] } as GetRelatedRecordsQuery, onRelatedLoaded });
    handleResponse({ data: { relatedRecords: [] } as GetRelatedRecordsQuery, onRelatedLoaded });

    expect(onRelatedLoaded).toHaveBeenNthCalledWith(1, [task]);
    expect(onRelatedLoaded).toHaveBeenNthCalledWith(2, []);
  });

  it("does nothing when data is absent", () => {
    const { handleResponse } = useResponseHandler();
    const onRelatedLoaded = vi.fn();
    handleResponse({ data: undefined, onRelatedLoaded });
    expect(onRelatedLoaded).not.toHaveBeenCalled();
  });
});
