import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { markUserSignOut, resetSessionExpiry } from "../api/lib/sessionExpiry";

import SignInController from "../features/auth/controllers/SignInController/SignInController";
import { RootStore } from "../stores/RootStore";
import { StoreProvider } from "../stores/StoreProvider";
import RequireAuth from "./RequireAuth";

const mocks = vi.hoisted(() => ({
  session: null as null | { access_token: string },
  signIn: vi.fn(),
  signInWithOAuth: vi.fn(),
  clearStore: vi.fn(),
  authListener: null as null | ((event: string, session: unknown) => void),
}));

vi.mock("../api/lib/supabaseClient", () => ({
  supabaseClient: {
    auth: {
      getSession: () => Promise.resolve({ data: { session: mocks.session } }),
      onAuthStateChange: (listener: (event: string, session: unknown) => void) => {
        mocks.authListener = listener;
        return { data: { subscription: { unsubscribe: vi.fn() } } };
      },
      setSession: () => Promise.resolve({ data: {}, error: null }),
      signInWithOAuth: (args: unknown) => mocks.signInWithOAuth(args),
    },
  },
}));
vi.mock("../api/lib/apolloClient", () => ({
  apolloClient: { clearStore: () => mocks.clearStore() },
}));
vi.mock("../api/queries/GetMe/useGetMe", () => ({
  default: () => ({ triggerAPI: vi.fn(), data: undefined, apiStatus: 0, apiError: null }),
}));
vi.mock("../api/mutations/SignIn/useSignIn", () => ({
  default: () => ({ triggerAPI: mocks.signIn, apiStatus: 0, apiError: null }),
}));

const renderAt = (path: string, store: RootStore = new RootStore()): void => {
  render(
    <MemoryRouter initialEntries={[path]}>
      <StoreProvider store={store}>
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

describe("RequireAuth, a session that ends (002 sub-plan 4.4)", () => {
  const EXPIRED_NOTICE = "Your session expired. Sign in again to continue.";

  beforeEach(() => {
    mocks.session = { access_token: "token" };
    resetSessionExpiry();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const signOutFromSupabase = async (): Promise<void> => {
    mocks.session = null;
    await act(async () => {
      mocks.authListener?.("SIGNED_OUT", null);
    });
  };

  it("002 T-4.5: a rejected session lands on sign-in with the notice and empty stores", async () => {
    const store = new RootStore();
    store.toast.show({ message: "Memory saved", linkLabel: "", linkTo: "" });
    renderAt("/records/reminders/r1", store);
    expect(await screen.findByText("Reminder r1 page")).toBeInTheDocument();

    await signOutFromSupabase();

    expect(await screen.findByText(EXPIRED_NOTICE)).toBeInTheDocument();
    expect(store.toast.current).toBeNull();
    expect(mocks.clearStore).toHaveBeenCalledTimes(1);
  });

  it("002 T-4.7: the user's own sign-out shows no notice and still empties the stores", async () => {
    renderAt("/");
    expect(await screen.findByText("Capture page")).toBeInTheDocument();

    markUserSignOut();
    await signOutFromSupabase();

    expect(await screen.findByText("Sign in", { selector: "div" })).toBeInTheDocument();
    expect(screen.queryByText(EXPIRED_NOTICE)).not.toBeInTheDocument();
    expect(mocks.clearStore).toHaveBeenCalledTimes(1);
  });

  it("002 T-4.6: a page opened with no session shows no notice", async () => {
    mocks.session = null;
    renderAt("/");

    expect(await screen.findByText("Sign in", { selector: "div" })).toBeInTheDocument();
    expect(screen.queryByText(EXPIRED_NOTICE)).not.toBeInTheDocument();
  });

  it.each(["/sign-in?reason=other", "/sign-in?reason=%3Cb%3E"])(
    "002 T-4.6: %s shows no notice",
    async (path) => {
      mocks.session = null;
      renderAt(path);

      expect(await screen.findByText("Sign in", { selector: "div" })).toBeInTheDocument();
      expect(screen.queryByText(EXPIRED_NOTICE)).not.toBeInTheDocument();
    },
  );
});
