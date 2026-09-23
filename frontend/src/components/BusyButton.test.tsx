import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import BusyButton from "./BusyButton";

describe("BusyButton (TC-1.23)", () => {
  it("shows its label when idle", () => {
    render(
      <BusyButton isBusy={false} busyLabel="Saving">
        Save changes
      </BusyButton>,
    );

    const button = screen.getByRole("button", { name: "Save changes" });
    expect(button).not.toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "false");
    expect(screen.queryByTestId("busy-spinner")).not.toBeInTheDocument();
  });

  it("shows a spinner only, keeps the label in the layout, and locks", () => {
    render(
      <BusyButton isBusy busyLabel="Saving">
        Save changes
      </BusyButton>,
    );

    const button = screen.getByRole("button", { name: "Saving" });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(screen.getByTestId("busy-spinner")).toBeInTheDocument();
    // Still rendered, only invisible, so the button keeps its width.
    expect(screen.getByText("Save changes")).toHaveClass("invisible");
    expect(screen.queryByText("Saving…")).not.toBeInTheDocument();
  });
});
