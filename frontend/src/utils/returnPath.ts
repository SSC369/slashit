import type { SignOutReason } from "../api/lib/sessionExpiry";

const RETURN_PARAM = "next";
const HOME_PATH = "/";
const REASON_PARAM = "reason";
const EXPIRED_REASON = "expired";

/** The sign-in URL that brings the reader back to `path` afterwards
 * (003 sub-plan 4.3, decision 1). Home needs no parameter. An expired session
 * adds `reason=expired`, which carries no user data (002 FR-23). */
export const buildSignInPath = (path: string, reason?: SignOutReason): string => {
  const params = new URLSearchParams();
  if (path !== HOME_PATH) params.set(RETURN_PARAM, path);
  if (reason === "EXPIRED") params.set(REASON_PARAM, EXPIRED_REASON);
  const query = params.toString();
  return query ? `/sign-in?${query}` : "/sign-in";
};

/** Whether sign-in was reached because the session expired (002 FR-23). Any
 * other value is ignored, so the parameter cannot inject copy. */
export const readIsSessionExpired = (search: string): boolean =>
  new URLSearchParams(search).get(REASON_PARAM) === EXPIRED_REASON;

/**
 * Where sign-in should land, read from its own query string. Only a path on
 * this origin is honoured: "//evil.example" and "https://..." fall back to
 * home, so the parameter cannot be used as an open redirect.
 */
export const readReturnPath = (search: string): string => {
  const path = new URLSearchParams(search).get(RETURN_PARAM);
  if (path === null || !path.startsWith("/") || path.startsWith("//") || path.includes("\\")) {
    return HOME_PATH;
  }
  return path;
};
