import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Toast, { TOAST_LIFETIME_MS } from "./Toast";

const toast = {
  id: "t1",
  message: "Reminder set for tomorrow, 7:00 PM",
  linkLabel: "View in Records",
  linkTo: "/records/reminders/r1",
};

const renderToast = (onDismiss: (id: string) => void) =>
  render(
    <MemoryRouter>
      <Toast toast={toast} onDismiss={onDismiss} />
    </MemoryRouter>,
  );

describe("Toast (TC-1.22)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows the message and its link as a status region", () => {
    renderToast(vi.fn());

    expect(screen.getByRole("status")).toHaveTextContent("Reminder set for tomorrow, 7:00 PM");
    expect(screen.getByRole("link", { name: "View in Records" })).toHaveAttribute(
      "href",
      "/records/reminders/r1",
    );
  });

  it("hides itself after four seconds", () => {
    const onDismiss = vi.fn();
    renderToast(onDismiss);

    act(() => vi.advanceTimersByTime(TOAST_LIFETIME_MS - 1));
    expect(onDismiss).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(1));
    expect(onDismiss).toHaveBeenCalledWith("t1");
  });

  it("pauses while hovered and resumes with the time that was left", () => {
    const onDismiss = vi.fn();
    renderToast(onDismiss);

    act(() => vi.advanceTimersByTime(3000));
    fireEvent.mouseEnter(screen.getByRole("status"));
    act(() => vi.advanceTimersByTime(10_000));
    expect(onDismiss).not.toHaveBeenCalled();

    fireEvent.mouseLeave(screen.getByRole("status"));
    act(() => vi.advanceTimersByTime(999));
    expect(onDismiss).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(1));
    expect(onDismiss).toHaveBeenCalledWith("t1");
  });

  it("closes on its close button", () => {
    const onDismiss = vi.fn();
    renderToast(onDismiss);

    fireEvent.click(screen.getByRole("button", { name: "Dismiss" }));

    expect(onDismiss).toHaveBeenCalledWith("t1");
  });
});
