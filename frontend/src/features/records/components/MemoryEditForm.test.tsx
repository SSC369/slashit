import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import MemoryEditForm from "./MemoryEditForm";

const renderForm = (text: string, onChange = vi.fn()) =>
  render(
    <MemoryEditForm
      draft={{ text, category: "LIFE" }}
      textError={null}
      banner="NONE"
      isSaving={false}
      isOffline={false}
      onChange={onChange}
      onSave={vi.fn()}
      onCancel={vi.fn()}
    />,
  );

describe("MemoryEditForm, F-3 of sub-plan 4.1", () => {
  it("counts characters and allows saving at the limit", () => {
    renderForm("x".repeat(500));

    expect(screen.getByText("500 / 500")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeEnabled();
  });

  it("blocks saving past 500 and says why (FR-18)", () => {
    renderForm("x".repeat(501));

    expect(screen.getByText("501 / 500")).toBeInTheDocument();
    expect(screen.getByText("A memory can be up to 500 characters.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });

  it("blocks saving empty text", () => {
    renderForm("   ");

    expect(screen.getByRole("button", { name: "Save changes" })).toBeDisabled();
  });

  it("changes the category without touching the text", () => {
    const onChange = vi.fn();
    renderForm("Learning Go", onChange);

    fireEvent.click(screen.getByRole("radio", { name: "Professional" }));

    expect(onChange).toHaveBeenCalledWith({ category: "PROFESSIONAL" });
  });
});
