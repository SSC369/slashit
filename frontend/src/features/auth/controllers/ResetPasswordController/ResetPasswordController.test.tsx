import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import ResetPasswordController from "./ResetPasswordController";

const { mockVerifyOtp, mockUpdateUser, mockSignOut, mockResetPasswordForEmail } = vi.hoisted(
  () => ({
    mockVerifyOtp: vi.fn(),
    mockUpdateUser: vi.fn(),
    mockSignOut: vi.fn(),
    mockResetPasswordForEmail: vi.fn(),
  }),
);

vi.mock("../../../../api/lib/supabaseClient", () => ({
  supabaseClient: {
    auth: {
      verifyOtp: (args: unknown) => mockVerifyOtp(args),
      updateUser: (args: unknown) => mockUpdateUser(args),
      signOut: () => mockSignOut(),
      resetPasswordForEmail: (email: string) => mockResetPasswordForEmail(email),
    },
  },
}));

const CODE_ERROR_COPY = "This code is wrong or has expired. Request a new one.";

const renderScreen = (email = "jordan@example.com") =>
  render(
    <MemoryRouter initialEntries={[`/reset-password?email=${encodeURIComponent(email)}`]}>
      <ResetPasswordController />
    </MemoryRouter>,
  );

const enterCode = (code: string): void => {
  fireEvent.paste(screen.getByLabelText("Digit 1 of 6"), {
    clipboardData: { getData: () => code },
  });
};

describe("ResetPasswordController", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("verifies the code as a recovery OTP for the address it was sent to", async () => {
    mockVerifyOtp.mockResolvedValue({ data: {}, error: null });

    renderScreen();
    enterCode("519362");

    expect(await screen.findByText("Set a new password")).toBeInTheDocument();
    expect(mockVerifyOtp).toHaveBeenCalledWith({
      email: "jordan@example.com",
      token: "519362",
      type: "recovery",
    });
  });

  // T-2.3: a wrong code and an expired code deliberately share one message
  // here (02-design.md §4/§8, NFR-2), unlike Verify email's two states. These
  // two cases assert that both Supabase responses land on the same copy.
  it("shows the shared wrong-or-expired message for a wrong code", async () => {
    mockVerifyOtp.mockResolvedValue({
      data: null,
      error: { code: "otp_expired", status: 403, message: "Token has expired or is invalid" },
    });

    renderScreen();
    enterCode("000000");

    expect(await screen.findByText(CODE_ERROR_COPY)).toBeInTheDocument();
    expect(screen.getByText("Enter the code")).toBeInTheDocument();
  });

  it("shows the same message for an expired code", async () => {
    mockVerifyOtp.mockResolvedValue({
      data: null,
      error: { code: "otp_expired", status: 401, message: "Email link is invalid or has expired" },
    });

    renderScreen();
    enterCode("111111");

    expect(await screen.findByText(CODE_ERROR_COPY)).toBeInTheDocument();
  });

  it("renders the rate-limited card instead of the code error on a throttle", async () => {
    mockVerifyOtp.mockResolvedValue({
      data: null,
      error: { code: "over_request_rate_limit", status: 429, message: "rate limited" },
    });

    renderScreen();
    enterCode("222222");

    expect(await screen.findByText("Too many attempts")).toBeInTheDocument();
    expect(
      screen.getByText("This code is now blocked. Request a new one in 15 minutes."),
    ).toBeInTheDocument();
    expect(screen.queryByText(CODE_ERROR_COPY)).not.toBeInTheDocument();
  });

  it("sets the new password, closes the recovery session and confirms", async () => {
    mockVerifyOtp.mockResolvedValue({ data: {}, error: null });
    mockUpdateUser.mockResolvedValue({ data: {}, error: null });
    mockSignOut.mockResolvedValue({ error: null });

    renderScreen();
    enterCode("519362");
    await screen.findByText("Set a new password");

    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "new-secret-1" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), {
      target: { value: "new-secret-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Set new password" }));

    expect(await screen.findByText("Password changed")).toBeInTheDocument();
    expect(screen.getByText("Sign in with your new password.")).toBeInTheDocument();
    expect(mockUpdateUser).toHaveBeenCalledWith({ password: "new-secret-1" });
    expect(mockSignOut).toHaveBeenCalled();
  });

  it("refuses a mismatched confirmation without calling Supabase", async () => {
    mockVerifyOtp.mockResolvedValue({ data: {}, error: null });

    renderScreen();
    enterCode("519362");
    await screen.findByText("Set a new password");

    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "new-secret-1" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), {
      target: { value: "different" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Set new password" }));

    expect(screen.getByText("Both passwords must match.")).toBeInTheDocument();
    expect(mockUpdateUser).not.toHaveBeenCalled();
  });
});
