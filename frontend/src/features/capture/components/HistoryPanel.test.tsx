import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { API_FAILED, API_FETCHING, API_INITIAL, API_SUCCESS } from "@/constants/apiConstants";
import HistoryPanel from "./HistoryPanel";

const { mockUseGetCaptureHistory, mockTriggerAPI } = vi.hoisted(() => ({
  mockUseGetCaptureHistory: vi.fn(),
  mockTriggerAPI: vi.fn(),
}));

vi.mock("@/api/queries/GetCaptureHistory/useGetCaptureHistory", () => ({
  default: () => mockUseGetCaptureHistory(),
}));

describe("HistoryPanel", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("T-4.11: renders nothing when closed", () => {
    mockUseGetCaptureHistory.mockReturnValue({
      triggerAPI: mockTriggerAPI,
      data: undefined,
      apiStatus: API_INITIAL,
      apiError: null,
    });

    const { container } = render(<HistoryPanel isOpen={false} onClose={vi.fn()} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("T-4.11: loading state shows skeleton rows before any data arrives", () => {
    mockUseGetCaptureHistory.mockReturnValue({
      triggerAPI: mockTriggerAPI,
      data: undefined,
      apiStatus: API_FETCHING,
      apiError: null,
    });

    render(<HistoryPanel isOpen onClose={vi.fn()} />);

    expect(screen.getByText("History")).toBeInTheDocument();
    expect(screen.queryByText("Nothing captured yet")).not.toBeInTheDocument();
  });

  it("T-4.11: error state shows a retry action", () => {
    mockUseGetCaptureHistory.mockReturnValue({
      triggerAPI: mockTriggerAPI,
      data: undefined,
      apiStatus: API_FAILED,
      apiError: new Error("network down"),
    });

    render(<HistoryPanel isOpen onClose={vi.fn()} />);

    expect(screen.getByText("Couldn't load your history")).toBeInTheDocument();
    screen.getByText("Retry").click();
    expect(mockTriggerAPI).toHaveBeenCalledWith({ cursor: null });
  });

  it("T-4.11: empty state shows once a load succeeds with no turns", () => {
    mockUseGetCaptureHistory.mockReturnValue({
      triggerAPI: mockTriggerAPI,
      data: { captureHistory: { items: [], nextCursor: null } },
      apiStatus: API_SUCCESS,
      apiError: null,
    });

    render(<HistoryPanel isOpen onClose={vi.fn()} />);

    expect(screen.getByText("Nothing captured yet")).toBeInTheDocument();
  });

  it("T-4.11: success state renders a turn's input text and outcome", () => {
    mockUseGetCaptureHistory.mockReturnValue({
      triggerAPI: mockTriggerAPI,
      data: {
        captureHistory: {
          items: [
            {
              id: "turn-1",
              inputText: "/add-task buy milk",
              outcome: "TASK_CREATED",
              resultingTaskId: "task-1",
              resultingPendingCaptureId: null,
              questionText: null,
              answerText: null,
              createdAt: new Date().toISOString(),
            },
          ],
          nextCursor: null,
        },
      },
      apiStatus: API_SUCCESS,
      apiError: null,
    });

    render(<HistoryPanel isOpen onClose={vi.fn()} />);

    expect(screen.getByText("/add-task buy milk")).toBeInTheDocument();
    expect(screen.getByText("Task created")).toBeInTheDocument();
  });

  it("one row per thread: a resolved question's earlier row is not shown separately", () => {
    mockUseGetCaptureHistory.mockReturnValue({
      triggerAPI: mockTriggerAPI,
      data: {
        captureHistory: {
          items: [
            {
              id: "turn-2",
              inputText: "/add-task",
              outcome: "TASK_CREATED",
              resultingTaskId: "task-1",
              resultingPendingCaptureId: "pending-1",
              questionText: "What should the task be called?",
              answerText: "Buy milk",
              createdAt: new Date().toISOString(),
            },
            {
              id: "turn-1",
              inputText: "/add-task",
              outcome: "QUESTION_ASKED",
              resultingTaskId: null,
              resultingPendingCaptureId: "pending-1",
              questionText: "What should the task be called?",
              answerText: null,
              createdAt: new Date().toISOString(),
            },
          ],
          nextCursor: null,
        },
      },
      apiStatus: API_SUCCESS,
      apiError: null,
    });

    render(<HistoryPanel isOpen onClose={vi.fn()} />);

    expect(screen.getByText("Task created")).toBeInTheDocument();
    expect(screen.queryByText("Question asked")).not.toBeInTheDocument();
    expect(screen.getAllByText(/What should the task be called\?/)).toHaveLength(1);
  });

  it("a still-open question keeps its own row", () => {
    mockUseGetCaptureHistory.mockReturnValue({
      triggerAPI: mockTriggerAPI,
      data: {
        captureHistory: {
          items: [
            {
              id: "turn-3",
              inputText: "/add-task",
              outcome: "QUESTION_ASKED",
              resultingTaskId: null,
              resultingPendingCaptureId: "pending-2",
              questionText: "What should the task be called?",
              answerText: null,
              createdAt: new Date().toISOString(),
            },
          ],
          nextCursor: null,
        },
      },
      apiStatus: API_SUCCESS,
      apiError: null,
    });

    render(<HistoryPanel isOpen onClose={vi.fn()} />);

    expect(screen.getByText("Question asked")).toBeInTheDocument();
  });

  it("F-2.3: shows the placeholder for a forgotten turn and a count-only /forget row", () => {
    mockUseGetCaptureHistory.mockReturnValue({
      triggerAPI: mockTriggerAPI,
      data: {
        captureHistory: {
          items: [
            {
              id: "turn-6",
              inputText: "/forget",
              outcome: "MEMORY_FORGOTTEN",
              resultingTaskId: null,
              resultingPendingCaptureId: null,
              questionText: null,
              answerText: null,
              forgotten: false,
              affectedCount: 2,
              createdAt: new Date().toISOString(),
            },
            {
              id: "turn-5",
              inputText: "",
              outcome: "MEMORY_SAVED",
              resultingTaskId: null,
              resultingPendingCaptureId: null,
              questionText: null,
              answerText: null,
              forgotten: true,
              affectedCount: null,
              createdAt: new Date().toISOString(),
            },
          ],
          nextCursor: null,
        },
      },
      apiStatus: API_SUCCESS,
      apiError: null,
    });

    render(<HistoryPanel isOpen onClose={vi.fn()} />);

    expect(screen.getByText("A memory was saved here and later forgotten")).toBeInTheDocument();
    expect(screen.getByText("Forgotten")).toBeInTheDocument();
    expect(screen.getByText("Forgot 2 memories")).toBeInTheDocument();
    expect(screen.getByText("/forget")).toBeInTheDocument();
  });
});
