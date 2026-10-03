import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ExpenseEditForm, { type ExpenseDraft } from "./ExpenseEditForm";

const draft: ExpenseDraft = {
  amountText: "850",
  description: "Dinner with friends",
  category: "FOOD",
  spentOn: "2026-10-01",
};

const renderForm = (overrides: Partial<ExpenseDraft> = {}, onChange = vi.fn()) =>
  render(
    <ExpenseEditForm
      draft={{ ...draft, ...overrides }}
      serverErrors={{ amount: null, description: null }}
      banner="NONE"
      isSaving={false}
      isOffline={false}
      onChange={onChange}
      onSave={vi.fn()}
      onCancel={vi.fn()}
    />,
  );

describe("ExpenseEditForm, F-5 of sub-plan 4.1", () => {
  it("saves a valid draft and counts the description", () => {
    renderForm();

    expect(screen.getByRole("button", { name: "Save changes" })).toBeEnabled();
    expect(screen.getByText("19 / 200")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Food" })).toHaveAttribute("aria-checked", "true");
  });

  it("blocks an amount of zero, with the field error (FR-21)", () => {
    renderForm({ amountText: "0" });

    expect(screen.getByText("Enter an amount above ₹0, such as 850 or 1,200.50.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });

  it("blocks a description over 200 characters (FR-13, FR-21)", () => {
    renderForm({ description: "x".repeat(214) });

    expect(screen.getByText("That is 214 characters. A description can be up to 200.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });

  it("chooses any date from the calendar, future included (FR-21)", () => {
    const onChange = vi.fn();
    renderForm({}, onChange);

    fireEvent.click(screen.getByRole("button", { name: "Date, Thu 1 Oct 2026" }));
    fireEvent.click(screen.getByRole("gridcell", { name: "Saturday 31 October 2026" }));

    expect(onChange).toHaveBeenCalledWith({ spentOn: "2026-10-31" });
  });
});
