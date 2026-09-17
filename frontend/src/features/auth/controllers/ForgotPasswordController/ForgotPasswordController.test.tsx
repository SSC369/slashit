import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import ForgotPasswordController from "./ForgotPasswordController";

const { mockResetPasswordForEmail } = vi.hoisted(() => ({
  mockResetPasswordForEmail: vi.fn(),
}));

vi.mock("../../../../api/lib/supabaseClient", () => ({
  supabaseClient: {
    auth: { resetPasswordForEmail: (email: string) => mockResetPasswordForEmail(email) },
  },
}));

const CONFIRMATION_COPY =
  "If an account exists for that address, we have sent a code to reset the password.";

const renderScreen = () =>
  render(
    <MemoryRouter>
      <ForgotPasswordController />
    </MemoryRouter>,
  );

const submitEmail = (email: string): void => {
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: email } });
  fireEvent.click(screen.getByRole("button", { name: "Send code" }));
};

describe("ForgotPasswordController", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  // T-2.2: the confirmation must be byte-identical whether or not the address
  // has an account. Supabase returns the same empty-error response either way,
  // so the test asserts the screen adds no branch of its own.
  it("shows the same confirmation copy for an address with an account", async () => {
    mockResetPasswordForEmail.mockResolvedValue({ data: {}, error: null });

    renderScreen();
    submitEmail("has-account@example.com");

    expect(await screen.findByText(CONFIRMATION_COPY)).toBeInTheDocument();
    expect(screen.getByText("Check your email")).toBeInTheDocument();
  });

  it("shows the same confirmation copy for an address with no account", async () => {
    mockResetPasswordForEmail.mockResolvedValue({ data: {}, error: null });

    renderScreen();
    submitEmail("no-account@example.com");

    expect(await screen.findByText(CONFIRMATION_COPY)).toBeInTheDocument();
    expect(screen.getByText("Check your email")).toBeInTheDocument();
  });

  it("never names the account's existence in the confirmation", async () => {
    mockResetPasswordForEmail.mockResolvedValue({ data: {}, error: null });

    renderScreen();
    submitEmail("someone@example.com");

    await screen.findByText(CONFIRMATION_COPY);
    expect(screen.queryByText(/no account/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/not registered/i)).not.toBeInTheDocument();
  });

  it("rejects a malformed address client-side without calling Supabase", () => {
    renderScreen();
    submitEmail("jordan@example");

    expect(screen.getByText("Enter a valid email address.")).toBeInTheDocument();
    expect(screen.getByText("Missing the domain part")).toBeInTheDocument();
    expect(mockResetPasswordForEmail).not.toHaveBeenCalled();
  });

  it("renders the rate-limited card on Supabase's send throttle", async () => {
    mockResetPasswordForEmail.mockResolvedValue({
      data: null,
      error: { code: "over_email_send_rate_limit", status: 400, message: "rate limited" },
    });

    renderScreen();
    submitEmail("jordan@example.com");

    expect(await screen.findByText("Too many requests")).toBeInTheDocument();
    expect(
      screen.getByText("Too many reset requests for this address. Try again in a few minutes."),
    ).toBeInTheDocument();
  });

  it("falls back to the generic retry error on a network failure", async () => {
    mockResetPasswordForEmail.mockResolvedValue({
      data: null,
      error: { code: undefined, status: 0, message: "Failed to fetch" },
    });

    renderScreen();
    submitEmail("jordan@example.com");

    expect(await screen.findByText("Something went wrong. Try again.")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Send code" })).toBeEnabled();
    });
  });
});
