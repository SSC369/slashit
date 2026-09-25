import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SignInController from "../features/auth/controllers/SignInController/SignInController";
import { RootStore } from "../stores/RootStore";
import { StoreProvider } from "../stores/StoreProvider";
import RequireAuth from "./RequireAuth";

const mocks = vi.hoisted(() => ({
  session: null as null | { access_token: string },
  signIn: vi.fn(),
  signInWithOAuth: vi.fn(),
}));

vi.mock("../api/lib/supabaseClient", () => ({
  supabaseClient: {
    auth: {
      getSession: () => Promise.resolve({ data: { session: mocks.session } }),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe: vi.fn() } } }),
      setSession: () => Promise.resolve({ data: {}, error: null }),
      signInWithOAuth: (args: unknown) => mocks.signInWithOAuth(args),
    },
  },
}));
vi.mock("../api/queries/GetMe/useGetMe", () => ({
  default: () => ({ triggerAPI: vi.fn(), data: undefined, apiStatus: 0, apiError: null }),
}));
vi.mock("../api/mutations/SignIn/useSignIn", () => ({
  default: () => ({ triggerAPI: mocks.signIn, apiStatus: 0, apiError: null }),
}));

const renderAt = (path: string): void => {
  render(
    <MemoryRouter initialEntries={[path]}>
      <StoreProvider store={new RootStore()}>
        <Routes>
          <Route path="/sign-in" element={<SignInController />} />
          <Route element={<RequireAuth />}>
            <Route path="/" element={<div>Capture page</div>} />
            <Route path="/records/reminders/:id" element={<div>Reminder r1 page</div>} />
          </Route>
        </Routes>
      </StoreProvider>
    </MemoryRouter>,
  );
};

describe("RequireAuth and sign-in, returning to the link", () => {
  beforeEach(() => {
    mocks.session = null;
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("TC-3.12: signed out on a reminder link, sign in, land on that reminder", async () => {
    renderAt("/records/reminders/r1");
    expect(await screen.findByText("Sign in", { selector: "div" })).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText("jordan@example.com"), {
      target: { value: "you@example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("••••••••••"), { target: { value: "secret-pass" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    mocks.session = { access_token: "token" };
    const signInArgs = mocks.signIn.mock.lastCall?.[0] as {
      onSignedIn: (session: { accessToken: string; refreshToken: string }) => Promise<void>;
    };
    const { onSignedIn } = signInArgs;
    await act(() => onSignedIn({ accessToken: "token", refreshToken: "refresh" }));
    await act(async () => {
      vi.advanceTimersByTime(1300);
    });

    expect(await screen.findByText("Reminder r1 page")).toBeInTheDocument();
  });

  it("TC-3.12: Continue with Google returns to the same link", async () => {
    renderAt("/records/reminders/r1");
    fireEvent.click(await screen.findByRole("button", { name: /Continue with Google/ }));

    expect(mocks.signInWithOAuth).toHaveBeenCalledWith(
      expect.objectContaining({
        options: expect.objectContaining({
          redirectTo: `${window.location.origin}/records/reminders/r1`,
        }),
      }),
    );
  });
});
