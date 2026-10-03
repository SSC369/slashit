import { describe, expect, it, vi } from "vitest";

import { buildEvent } from "../../../testing/eventFixture";
import { buildMemory } from "../../../testing/memoryFixture";
import { buildSearchResults } from "../../../testing/searchFixture";
import type { AnswerPendingCaptureMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("AnswerPendingCapture responseHandler, F-3.3 of sub-plan 4.3", () => {
  it("hands a fact answer that conflicts to onMemoryConflictAsked", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryConflictAsked = vi.fn();
    const old = buildMemory({ text: "Preferred airline is Emirates" });
    const data: AnswerPendingCaptureMutation = {
      answerPendingCapture: {
        __typename: "MemoryConflictAsked",
        pendingCaptureId: "p2",
        question: "Which is correct?",
        newText: "My preferred airline is Qatar Airways",
        category: null,
        conflicting: [old],
      },
    };

    handleResponse({ data, onMemoryConflictAsked });

    expect(onMemoryConflictAsked).toHaveBeenCalledWith({
      pendingCaptureId: "p2",
      newText: "My preferred airline is Qatar Airways",
      category: null,
      conflicting: [old],
    });
  });
});

describe("AnswerPendingCapture responseHandler, epic 005's members", () => {
  it("hands SearchResults to onSearchResults whole", () => {
    const { handleResponse } = useResponseHandler();
    const onSearchResults = vi.fn();
    const results = buildSearchResults();
    const data: AnswerPendingCaptureMutation = { answerPendingCapture: { __typename: "SearchResults", ...results } };

    handleResponse({ data, onSearchResults });

    expect(onSearchResults).toHaveBeenCalledWith({ __typename: "SearchResults", ...results });
  });

  it("hands SearchTooLong to onSearchTooLong with its length and limit", () => {
    const { handleResponse } = useResponseHandler();
    const onSearchTooLong = vi.fn();
    const data: AnswerPendingCaptureMutation = {
      answerPendingCapture: { __typename: "SearchTooLong", length: 612, limit: 500 },
    };

    handleResponse({ data, onSearchTooLong });

    expect(onSearchTooLong).toHaveBeenCalledWith({ length: 612, limit: 500 });
  });
});

describe("AnswerPendingCapture responseHandler, epic 007's members", () => {
  it("hands EventCreated's event and the alerts not set to onEventCreated", () => {
    const { handleResponse } = useResponseHandler();
    const onEventCreated = vi.fn();
    const event = buildEvent();
    const alertsNotSet = [{ leadMinutes: 2880, text: "2 days before", reason: "PASSED" as const }];
    const data: AnswerPendingCaptureMutation = {
      answerPendingCapture: { __typename: "EventCreated", event, alertsNotSet },
    };

    handleResponse({ data, onEventCreated });

    expect(onEventCreated).toHaveBeenCalledWith({ event, alertsNotSet });
  });

  it("hands EventsListed's events to onEventsListed", () => {
    const { handleResponse } = useResponseHandler();
    const onEventsListed = vi.fn();
    const events = [buildEvent()];
    const data: AnswerPendingCaptureMutation = { answerPendingCapture: { __typename: "EventsListed", events } };

    handleResponse({ data, onEventsListed });

    expect(onEventsListed).toHaveBeenCalledWith(events);
  });

  it("hands EventLimitReached to onEventLimitReached", () => {
    const { handleResponse } = useResponseHandler();
    const onEventLimitReached = vi.fn();
    const data: AnswerPendingCaptureMutation = {
      answerPendingCapture: { __typename: "EventLimitReached", message: "full", limit: 500 },
    };

    handleResponse({ data, onEventLimitReached });

    expect(onEventLimitReached).toHaveBeenCalledWith({ message: "full", limit: 500 });
  });
});
