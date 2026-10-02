import { describe, expect, it, vi } from "vitest";

import { buildEvent } from "../../../testing/eventFixture";
import type { GetEventQuery } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("GetEvent responseHandler", () => {
  it("hands a found event to onEventLoaded", () => {
    const { handleResponse } = useResponseHandler();
    const onEventLoaded = vi.fn();
    const event = { __typename: "Event" as const, ...buildEvent() };

    handleResponse({ data: { event }, onEventLoaded });

    expect(onEventLoaded).toHaveBeenCalledWith(event);
  });

  it("calls onEventNotFound for EventNotFound", () => {
    const { handleResponse } = useResponseHandler();
    const onEventNotFound = vi.fn();
    const data: GetEventQuery = { event: { __typename: "EventNotFound", message: "gone" } };

    handleResponse({ data, onEventNotFound });

    expect(onEventNotFound).toHaveBeenCalledWith("gone");
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { event: { __typename: "Unknown" } } as unknown as GetEventQuery;

    expect(() => handleResponse({ data })).toThrow("Unhandled EventResult type");
  });
});
