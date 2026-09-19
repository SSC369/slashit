import { describe, expect, it, vi } from "vitest";

import { useResponseHandler } from "./responseHandler";
import type { SignInMutation } from "./operation.generated";

describe("SignIn responseHandler", () => {
  it("calls onSignedIn with the session for a SignedIn result", () => {
    const { handleResponse } = useResponseHandler();
    const onSignedIn = vi.fn();
    const data: SignInMutation = {
      signIn: {
        __typename: "SignedIn",
        accessToken: "at",
        refreshToken: "rt",
        expiresIn: 3600,
      },
    };

    handleResponse({ data, onSignedIn });

    expect(onSignedIn).toHaveBeenCalledWith({
      accessToken: "at",
      refreshToken: "rt",
      expiresIn: 3600,
    });
  });

  it("calls onInvalidCredentials for an InvalidCredentials result", () => {
    const { handleResponse } = useResponseHandler();
    const onInvalidCredentials = vi.fn();
    const data: SignInMutation = {
      signIn: { __typename: "InvalidCredentials", message: "Incorrect email or password" },
    };

    handleResponse({ data, onInvalidCredentials });

    expect(onInvalidCredentials).toHaveBeenCalledWith("Incorrect email or password");
  });

  it("calls onAccountLocked with the message and retryAfter for an AccountLocked result", () => {
    const { handleResponse } = useResponseHandler();
    const onAccountLocked = vi.fn();
    const data: SignInMutation = {
      signIn: {
        __typename: "AccountLocked",
        message: "Too many attempts. Try again in 15 minutes.",
        retryAfter: "2026-09-19T00:15:00Z",
      },
    };

    handleResponse({ data, onAccountLocked });

    expect(onAccountLocked).toHaveBeenCalledWith(
      "Too many attempts. Try again in 15 minutes.",
      "2026-09-19T00:15:00Z",
    );
  });

  it("calls onAccountNotVerified for an AccountNotVerified result", () => {
    const { handleResponse } = useResponseHandler();
    const onAccountNotVerified = vi.fn();
    const data: SignInMutation = {
      signIn: { __typename: "AccountNotVerified", message: "Verify your email before signing in" },
    };

    handleResponse({ data, onAccountNotVerified });

    expect(onAccountNotVerified).toHaveBeenCalledWith("Verify your email before signing in");
  });

  it("calls onProviderUnavailable for an AuthProviderUnavailable result", () => {
    const { handleResponse } = useResponseHandler();
    const onProviderUnavailable = vi.fn();
    const data: SignInMutation = {
      signIn: {
        __typename: "AuthProviderUnavailable",
        message: "Sign-in is temporarily unavailable. Try again shortly.",
      },
    };

    handleResponse({ data, onProviderUnavailable });

    expect(onProviderUnavailable).toHaveBeenCalledWith(
      "Sign-in is temporarily unavailable. Try again shortly.",
    );
  });

  it("does nothing when data is absent", () => {
    const { handleResponse } = useResponseHandler();
    expect(() => handleResponse({ data: null })).not.toThrow();
  });

  it("throws via assertNever for an unhandled typename", () => {
    const { handleResponse } = useResponseHandler();
    const data = {
      signIn: { __typename: "SomethingNew" },
    } as unknown as SignInMutation;

    expect(() => handleResponse({ data })).toThrow(/Unhandled SignInResult type/);
  });
});
