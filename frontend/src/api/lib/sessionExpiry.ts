import { supabaseClient } from "./supabaseClient";

/** Why the session ended. Only EXPIRED shows the sign-in notice (002 FR-23). */
export type SignOutReason = "EXPIRED" | "USER";

/** The code the server puts on every authentication refusal (002 AD-8). */
export const UNAUTHENTICATED_CODE = "UNAUTHENTICATED";

/** The close code the server sends a WebSocket whose token it rejects. */
export const REJECTED_SOCKET_CLOSE_CODE = 4403;

let isEnding = false;
let isUserSignOut = false;

/**
 * Ends a session the server rejected. Runs once until the next sign-in, however
 * many requests fail together. Local scope: other devices keep their sessions.
 * supabase-js removes the stored session even when its sign-out call fails,
 * and emits SIGNED_OUT, which RequireAuth turns into the redirect.
 */
export const endExpiredSession = async (): Promise<void> => {
  if (isEnding) return;
  // Set before the first await, or concurrent callers all pass the check.
  isEnding = true;
  const { data } = await supabaseClient.auth.getSession();
  // No session means nothing to end: an already signed-out page is not expired.
  if (data.session === null) {
    isEnding = false;
    return;
  }
  await supabaseClient.auth.signOut({ scope: "local" });
};

/** AppShell calls this before its own signOut(), so no notice shows. */
export const markUserSignOut = (): void => {
  isUserSignOut = true;
};

/** RequireAuth reads this once per SIGNED_OUT event. */
export const takeSignOutReason = (): SignOutReason => {
  const reason: SignOutReason = isUserSignOut ? "USER" : "EXPIRED";
  isUserSignOut = false;
  return reason;
};

/** Called on SIGNED_IN, so the next rejected session is handled again. */
export const resetSessionExpiry = (): void => {
  isEnding = false;
  isUserSignOut = false;
};
