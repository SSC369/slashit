import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { EventFieldsFragment } from "../../../fragments/EventFields.generated";
import { buildEvent } from "../../../testing/eventFixture";
import {
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
        alertsNotSet={[]}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("Event saved")).toBeInTheDocument();
    expect(screen.getByText("Mon 12 Oct, all day").nextSibling).toHaveTextContent("No time given, so all day");
    expect(screen.getByText("Every year").nextSibling).toHaveTextContent("Read from “birthday”");
    expect(screen.getByText("1 day before").nextSibling).toHaveTextContent("Sun 11 Oct, 9:00 AM");
    expect(screen.getByText("At your default reminder time")).toBeInTheDocument();
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
          alerts: [{ leadMinutes: 60, text: "1 hour before", firesAt: "2026-10-09T09:30:00Z" }],
        })}
        alertsNotSet={[]}
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
        event={buildEvent({ eventStatus: "PAST", repeatYearly: false, alerts: [] })}
        alertsNotSet={[]}
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
        alertsNotSet={[]}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("5 days")).toBeInTheDocument();
  });

  it("opens the saved event in Records", () => {
    const onOpenEvent = vi.fn();
    render(<EventSavedCard event={buildEvent({ id: "e9" })} alertsNotSet={[]} onOpenEvent={onOpenEvent} />);

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

describe("Event alerts on the saved card, T-2.10 of sub-plan 4.2 (F-1)", () => {
  const dentist = (overrides: Partial<EventFieldsFragment> = {}): EventFieldsFragment =>
    buildEvent({
      title: "Dentist",
      allDay: false,
      repeatYearly: false,
      startTime: "16:00",
      startsAt: "2026-10-09T10:30:00Z",
      ...overrides,
    });

  it("lists every alert soonest first with when it fires (EventAlerts)", () => {
    render(
      <EventSavedCard
        event={dentist({
          alerts: [
            { leadMinutes: 1440, text: "1 day before", firesAt: "2026-10-08T10:30:00Z" },
            { leadMinutes: 60, text: "1 hour before", firesAt: "2026-10-09T09:30:00Z" },
          ],
          alertNotes: ["You named 1 hour before twice, so it is set once"],
        })}
        alertsNotSet={[]}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("Alerts")).toBeInTheDocument();
    expect(screen.getByText("1 day before").nextSibling).toHaveTextContent("Thu 8 Oct, 4:00 PM");
    expect(screen.getByText("1 hour before").nextSibling).toHaveTextContent("Fri 9 Oct, 3:00 PM");
    expect(screen.getByText("You named 1 hour before twice, so it is set once")).toBeInTheDocument();
    expect(screen.queryByText(/not set/)).not.toBeInTheDocument();
  });

  it("says which alert passed and that the other is set (EventAlertsPassed)", () => {
    render(
      <EventSavedCard
        event={dentist({
          startsAt: "2026-10-02T18:30:00Z",
          alerts: [{ leadMinutes: 60, text: "1 hour before", firesAt: "2026-10-02T17:30:00Z" }],
        })}
        alertsNotSet={[{ leadMinutes: 2880, text: "2 days before", reason: "PASSED" }]}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("2 days before").nextSibling).toHaveTextContent("Not set");
    expect(screen.getByText("1 of 2 alerts was not set")).toBeInTheDocument();
    expect(
      screen.getByText("2 days before is Thu 1 Oct, which has already passed. The other alert is set."),
    ).toBeInTheDocument();
  });

  it("asks for a later alert when the only one passed (EventAlertNotSet)", () => {
    render(
      <EventSavedCard
        event={dentist({ startsAt: "2026-10-02T18:30:00Z", alerts: [] })}
        alertsNotSet={[{ leadMinutes: 2880, text: "2 days before", reason: "PASSED" }]}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("Alert")).toBeInTheDocument();
    expect(screen.getByText("The alert was not set")).toBeInTheDocument();
    expect(screen.getByText(/Edit the event to choose a later alert\./)).toBeInTheDocument();
  });

  it("names the alerts left over the reminder cap (EventAlertsCap)", () => {
    render(
      <EventSavedCard
        event={dentist({
          alerts: [{ leadMinutes: 60, text: "1 hour before", firesAt: "2026-10-09T09:30:00Z" }],
        })}
        alertsNotSet={[
          { leadMinutes: 1440, text: "1 day before", reason: "CAP" },
          { leadMinutes: 10080, text: "1 week before", reason: "CAP" },
        ]}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("2 of 3 alerts were not set")).toBeInTheDocument();
    expect(
      screen.getByText(
        "You have 100 active reminders and alerts, the most Slashit holds. The alerts that fire first were set. Free one up, then add 1 day before and 1 week before in Edit.",
      ),
    ).toBeInTheDocument();
  });

  it("tells the only alert over the cap how to free one up", () => {
    render(
      <EventSavedCard
        event={dentist({ alerts: [] })}
        alertsNotSet={[{ leadMinutes: 60, text: "1 hour before", reason: "CAP" }]}
        onOpenEvent={vi.fn()}
      />,
    );

    expect(screen.getByText("The alert was not set")).toBeInTheDocument();
    expect(screen.getByText(/Mark a reminder done or remove an alert, then add it here\./)).toBeInTheDocument();
  });

  it("draws no Alerts field for an event without one", () => {
    render(<EventSavedCard event={dentist({ alerts: [] })} alertsNotSet={[]} onOpenEvent={vi.fn()} />);

    expect(screen.queryByText("Alert")).not.toBeInTheDocument();
    expect(screen.queryByText("Alerts")).not.toBeInTheDocument();
  });
});
