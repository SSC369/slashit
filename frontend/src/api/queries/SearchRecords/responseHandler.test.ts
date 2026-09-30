import { describe, expect, it, vi } from "vitest";

import { buildTask } from "@/testing/searchFixture";
import { useResponseHandler } from "./responseHandler";
import type { SearchRecordsQuery } from "./operation.generated";

describe("SearchRecords responseHandler", () => {
  it("hands a page to onPageLoaded", () => {
    const { handleResponse } = useResponseHandler();
    const onPageLoaded = vi.fn();
    const data = {
      search: {
        __typename: "SearchPage",
        query: "career",
        total: 1,
        otherTypesTotal: 0,
        meaningUnavailable: false,
        hits: [{ __typename: "Task", ...buildTask() }],
      },
    } as SearchRecordsQuery;

    handleResponse({ data, onPageLoaded });

    expect(onPageLoaded).toHaveBeenCalledWith(
      expect.objectContaining({ query: "career", total: 1, otherTypesTotal: 0 }),
    );
  });

  it("hands a refusal to onTooLong", () => {
    const { handleResponse } = useResponseHandler();
    const onTooLong = vi.fn();
    const data = { search: { __typename: "SearchTooLong", length: 612, limit: 500 } } as SearchRecordsQuery;

    handleResponse({ data, onTooLong });

    expect(onTooLong).toHaveBeenCalledWith(612, 500);
  });
});
