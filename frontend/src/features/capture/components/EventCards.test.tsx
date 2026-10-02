import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { buildEvent } from "../../../testing/eventFixture";
import {
  EventAlertChoiceCard,
  EventLimitNote,
  EventListCard,
  EventListFailedNote,
  EventSavedCard,
} from "./EventCards";

describe("Event capture cards, T-1.10 of sub-plan 4.1", () => {
  it("echoes every resolved field, each note under the field it explains (Main)", () => {
    render(
      <EventSavedCard
        event={buildEvent({ whenNotes: ["No time given, so all day", "Read from “birthday”"] })}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("Event saved")).toBeInTheDocument();
    expect(screen.getByText("Mon 12 Oct, all day").nextSibling).toHaveTextContent("No time given, so all day");
    expect(screen.getByText("Every year").nextSibling).toHaveTextContent("Read from “birthday”");
    expect(screen.getByText("1 day before").nextSibling).toHaveTextContent("your default reminder time");
  });

  it("shows location for a timed event and no default-time note on its alert", () => {
    render(
      <EventSavedCard
        event={buildEvent({
          title: "Dentist",
          allDay: false,
          repeatYearly: false,
          location: "Apollo Clinic",
          startTime: "16:00",
          alertText: "1 hour before",
          alertFiresAt: "2026-10-09T09:30:00Z",
        })}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("Apollo Clinic")).toBeInTheDocument();
    expect(screen.getByText("Does not repeat")).toBeInTheDocument();
    expect(screen.getByText("1 hour before").nextSibling).toHaveTextContent("Fri 9 Oct, 3:00 PM");
    expect(screen.queryByText(/default reminder time/)).not.toBeInTheDocument();
  });

  it("shows a past event's status where its repeat would go (FR-5)", () => {
    render(
      <EventSavedCard
        event={buildEvent({ eventStatus: "PAST", repeatYearly: false, alertText: null, alertFiresAt: null })}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("Past")).toBeInTheDocument();
    expect(screen.getByText("Kept in Records, not listed by /events")).toBeInTheDocument();
    expect(screen.queryByText("Repeat")).not.toBeInTheDocument();
  });

  it("counts an all-day range's days when the server gives no note (FR-6)", () => {
    render(
      <EventSavedCard
        event={buildEvent({ occurrenceEndDate: "2026-10-16", whenText: "Mon 12 to Fri 16 Oct, all day" })}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("5 days")).toBeInTheDocument();
  });

  it("opens the saved event in Records", () => {
    const onOpenEvent = vi.fn();
    render(<EventSavedCard event={buildEvent({ id: "e9" })} onOpenEvent={onOpenEvent} />);

    fireEvent.click(screen.getByRole("button", { name: /Open in Records/ }));

    expect(onOpenEvent).toHaveBeenCalledWith("e9");
  });

  it("groups /events by month with counts, soonest first (EventsList, FR-24)", () => {
    render(
      <EventListCard
        events={[
          buildEvent({ id: "a", occurrenceDate: "2026-10-09", title: "Dentist", repeatYearly: false }),
          buildEvent({ id: "b", occurrenceDate: "2026-10-12" }),
          buildEvent({ id: "c", occurrenceDate: "2026-11-21", title: "Sam's wedding", repeatYearly: false }),
        ]}
        onOpenEvent={vi.fn()}
        onOpenEvents={vi.fn()}
      />,
    );

    expect(screen.getByText("3 upcoming events · soonest first")).toBeInTheDocument();
    expect(screen.getByText("October 2026").nextSibling).toHaveTextContent("2");
    expect(screen.getByText("November 2026").nextSibling).toHaveTextContent("1");
    expect(screen.getByLabelText("Monday 12 October")).toHaveTextContent("12Mon");
    expect(screen.getAllByText("Yearly")).toHaveLength(1);
  });

  it("opens a row on Enter, one tab stop each (design §7)", () => {
    const onOpenEvent = vi.fn();
    render(<EventListCard events={[buildEvent({ id: "e3" })]} onOpenEvent={onOpenEvent} onOpenEvents={vi.fn()} />);

    fireEvent.keyDown(screen.getByText("Mom's birthday").closest("[role=button]") as Element, { key: "Enter" });

    expect(onOpenEvent).toHaveBeenCalledWith("e3");
  });

  it("draws the empty /events card with an example", () => {
    render(<EventListCard events={[]} onOpenEvent={vi.fn()} onOpenEvents={vi.fn()} />);

    expect(screen.getByText("No upcoming events")).toBeInTheDocument();
    expect(screen.getByText("/add-event Mom's birthday Oct 12")).toBeInTheDocument();
  });

  it("asks which alert, offering each lead and No alert (FR-16)", () => {
    const onChoose = vi.fn();
    render(
      <EventAlertChoiceCard
        question="Which alert should I keep?"
        choices={[
          { leadMinutes: 10080, label: "1 week before · Sat 14 Nov" },
          { leadMinutes: 1440, label: "1 day before · Fri 20 Nov" },
        ]}
        isBusy={false}
        error={null}
        onChoose={onChoose}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "1 day before · Fri 20 Nov" }));
    fireEvent.click(screen.getByRole("button", { name: "No alert" }));

    expect(onChoose).toHaveBeenNthCalledWith(1, "1440");
    expect(onChoose).toHaveBeenNthCalledWith(2, "none");
    expect(screen.getByText("An event can have one alert. The event is saved once you pick.")).toBeInTheDocument();
  });

  it("disables the choices while an answer is in flight", () => {
    render(
      <EventAlertChoiceCard
        question="Which alert should I keep?"
        choices={[{ leadMinutes: 60, label: "1 hour before" }]}
        isBusy
        error={null}
        onChoose={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "No alert" })).toBeDisabled();
  });

  it("refuses the 501st event with the design's copy (FR-31)", () => {
    render(<EventLimitNote />);

    expect(screen.getByText("You have 500 upcoming events, the most Slashit holds.")).toBeInTheDocument();
    expect(screen.getByText(/Past events do not count\./)).toBeInTheDocument();
  });

  it("offers Try again when /events could not load", () => {
    const onRetry = vi.fn();
    render(<EventListFailedNote onRetry={onRetry} />);

    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(screen.getByText("Couldn't load your events")).toBeInTheDocument();
    expect(onRetry).toHaveBeenCalled();
  });
});
