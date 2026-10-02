import { describe, expect, it, vi } from "vitest";

import { buildEvent } from "../../../testing/eventFixture";
import { buildMemory } from "../../../testing/memoryFixture";
import { buildSearchResults } from "../../../testing/searchFixture";
import type { SubmitCaptureMutation } from "./operation.generated";
import { useResponseHandler } from "./responseHandler";

describe("SubmitCapture responseHandler, epic 004's members", () => {
  it("hands MemorySaved's memory and caution to onMemorySaved", () => {
    const { handleResponse } = useResponseHandler();
    const onMemorySaved = vi.fn();
    const memory = buildMemory();
    const data: SubmitCaptureMutation = {
      submitCapture: { __typename: "MemorySaved", memory, secretCaution: "CREDENTIAL" },
    };

    handleResponse({ data, onMemorySaved });

    expect(onMemorySaved).toHaveBeenCalledWith({ memory, secretCaution: "CREDENTIAL" });
  });

  it("hands MemoriesListed to onMemoriesListed with its search text", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoriesListed = vi.fn();
    const data: SubmitCaptureMutation = {
      submitCapture: { __typename: "MemoriesListed", memories: [], searchText: "visa" },
    };

    handleResponse({ data, onMemoriesListed });

    expect(onMemoriesListed).toHaveBeenCalledWith({ memories: [], searchText: "visa" });
  });

  it("hands MemoryConflictAsked to onMemoryConflictAsked", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryConflictAsked = vi.fn();
    const old = buildMemory({ text: "Preferred airline is Emirates" });
    const data: SubmitCaptureMutation = {
      submitCapture: {
        __typename: "MemoryConflictAsked",
        pendingCaptureId: "p1",
        question: "Which is correct?",
        newText: "My preferred airline is Qatar Airways",
        category: "PERSONAL",
        conflicting: [old],
      },
    };

    handleResponse({ data, onMemoryConflictAsked });

    expect(onMemoryConflictAsked).toHaveBeenCalledWith({
      pendingCaptureId: "p1",
      newText: "My preferred airline is Qatar Airways",
      category: "PERSONAL",
      conflicting: [old],
    });
  });

  it("hands MemoryTooLong to onMemoryTooLong", () => {
    const { handleResponse } = useResponseHandler();
    const onMemoryTooLong = vi.fn();
    const data: SubmitCaptureMutation = {
      submitCapture: { __typename: "MemoryTooLong", message: "m", length: 612, limit: 500 },
    };

    handleResponse({ data, onMemoryTooLong });

    expect(onMemoryTooLong).toHaveBeenCalledWith({ message: "m", length: 612, limit: 500 });
  });

  it("throws on a member it does not know", () => {
    const { handleResponse } = useResponseHandler();
    const data = { submitCapture: { __typename: "Unknown" } } as unknown as SubmitCaptureMutation;

    expect(() => handleResponse({ data })).toThrow("Unhandled CaptureResult type");
  });
});

describe("SubmitCapture responseHandler, epic 005's members", () => {
  it("hands SearchResults to onSearchResults whole", () => {
    const { handleResponse } = useResponseHandler();
    const onSearchResults = vi.fn();
    const results = buildSearchResults();
    const data: SubmitCaptureMutation = { submitCapture: { __typename: "SearchResults", ...results } };

    handleResponse({ data, onSearchResults });

    expect(onSearchResults).toHaveBeenCalledWith({ __typename: "SearchResults", ...results });
  });

  it("hands SearchTooLong to onSearchTooLong with its length and limit", () => {
    const { handleResponse } = useResponseHandler();
    const onSearchTooLong = vi.fn();
    const data: SubmitCaptureMutation = {
      submitCapture: { __typename: "SearchTooLong", length: 612, limit: 500 },
    };

    handleResponse({ data, onSearchTooLong });

    expect(onSearchTooLong).toHaveBeenCalledWith({ length: 612, limit: 500 });
  });
});

describe("SubmitCapture responseHandler, epic 007's members", () => {
  it("hands EventCreated's event to onEventCreated", () => {
    const { handleResponse } = useResponseHandler();
    const onEventCreated = vi.fn();
    const event = buildEvent();
    const data: SubmitCaptureMutation = { submitCapture: { __typename: "EventCreated", event } };

    handleResponse({ data, onEventCreated });

    expect(onEventCreated).toHaveBeenCalledWith(event);
  });

  it("hands EventsListed's events to onEventsListed", () => {
    const { handleResponse } = useResponseHandler();
    const onEventsListed = vi.fn();
    const events = [buildEvent()];
    const data: SubmitCaptureMutation = { submitCapture: { __typename: "EventsListed", events } };

    handleResponse({ data, onEventsListed });

    expect(onEventsListed).toHaveBeenCalledWith(events);
  });

  it("hands EventLimitReached to onEventLimitReached", () => {
    const { handleResponse } = useResponseHandler();
    const onEventLimitReached = vi.fn();
    const data: SubmitCaptureMutation = {
      submitCapture: { __typename: "EventLimitReached", message: "full", limit: 500 },
    };

    handleResponse({ data, onEventLimitReached });

    expect(onEventLimitReached).toHaveBeenCalledWith({ message: "full", limit: 500 });
  });

  it("hands EventAlertChoiceAsked's choices to onEventAlertChoiceAsked", () => {
    const { handleResponse } = useResponseHandler();
    const onEventAlertChoiceAsked = vi.fn();
    const data: SubmitCaptureMutation = {
      submitCapture: {
        __typename: "EventAlertChoiceAsked",
        pendingCaptureId: "pc-1",
        question: "Which alert should I keep?",
        choices: [{ leadMinutes: 60, label: "1 hour before" }],
      },
    };

    handleResponse({ data, onEventAlertChoiceAsked });

    expect(onEventAlertChoiceAsked).toHaveBeenCalledWith({
      pendingCaptureId: "pc-1",
      question: "Which alert should I keep?",
      choices: [{ leadMinutes: 60, label: "1 hour before" }],
    });
  });
});
