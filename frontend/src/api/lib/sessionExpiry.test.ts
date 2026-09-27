import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  endExpiredSession,
  markUserSignOut,
  resetSessionExpiry,
  takeSignOutReason,
} from "./sessionExpiry";

const mocks = vi.hoisted(() => ({
  session: null as null | { access_token: string },
  signOut: vi.fn(),
}));

vi.mock("./supabaseClient", () => ({
  supabaseClient: {
    auth: {
      getSession: () => Promise.resolve({ data: { session: mocks.session } }),
      signOut: (args: unknown) => mocks.signOut(args),
    },
  },
}));

describe("sessionExpiry", () => {
  beforeEach(() => {
    mocks.session = { access_token: "token" };
    mocks.signOut.mockResolvedValue({ error: null });
    resetSessionExpiry();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("002 T-4.4: three rejections at once sign out once, on this device only", async () => {
    await Promise.all([
      endExpiredSession(),
      endExpiredSession(),
      endExpiredSession(),
    ]);

    expect(mocks.signOut).toHaveBeenCalledTimes(1);
    expect(mocks.signOut).toHaveBeenCalledWith({ scope: "local" });
  });

  it("002 T-4.4: does nothing when there is no session to end", async () => {
    mocks.session = null;

    await endExpiredSession();

    expect(mocks.signOut).not.toHaveBeenCalled();
  });

  it("002 T-4.4: handles a rejection again after the next sign-in", async () => {
    await endExpiredSession();
    resetSessionExpiry();
    await endExpiredSession();

    expect(mocks.signOut).toHaveBeenCalledTimes(2);
  });

  it("reports EXPIRED unless the user asked, and forgets the ask once read", () => {
    expect(takeSignOutReason()).toBe("EXPIRED");

    markUserSignOut();
    expect(takeSignOutReason()).toBe("USER");
    expect(takeSignOutReason()).toBe("EXPIRED");
  });
});
