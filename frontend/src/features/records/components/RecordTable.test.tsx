import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { buildEvent } from "../../../testing/eventFixture";
import RecordTable from "./RecordTable";

describe("RecordTable, epic 007's All tab (RecordsAllEvents, FR-26)", () => {
  it("draws an event with its diamond, its start and its status", () => {
    const event = buildEvent({ eventStatus: "HAPPENING_NOW" });
    const onOpenRecord = vi.fn();
    render(<RecordTable records={[{ kind: "EVENT", event }]} onOpenRecord={onOpenRecord} />);

    fireEvent.click(screen.getByText("Mom's birthday"));

    expect(screen.getByRole("img", { name: "Event" })).toBeInTheDocument();
    expect(screen.getByText("Happening now")).toBeInTheDocument();
    expect(screen.getByText("Events carry a diamond marker")).toBeInTheDocument();
    expect(onOpenRecord).toHaveBeenCalledWith({ kind: "EVENT", event });
  });
});
