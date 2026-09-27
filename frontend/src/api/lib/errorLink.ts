import { CombinedGraphQLErrors, ServerError } from "@apollo/client/errors";
import { ErrorLink } from "@apollo/client/link/error";
import { NEVER } from "rxjs";

import { UNAUTHENTICATED_CODE, endExpiredSession } from "./sessionExpiry";

const HTTP_UNAUTHORIZED = 401;

const isSessionRejected = (error: unknown): boolean =>
  (CombinedGraphQLErrors.is(error) &&
    error.errors.some(
      (graphQLError) => graphQLError.extensions?.code === UNAUTHENTICATED_CODE,
    )) ||
  (ServerError.is(error) && error.statusCode === HTTP_UNAUTHORIZED);

/**
 * Ends the session when the server refuses it (002 FR-23). The failed result is
 * held back rather than passed on, so no screen draws a "Not authenticated"
 * card in the moment before the redirect to sign-in replaces it.
 */
export const errorLink = new ErrorLink(({ error }) => {
  if (!isSessionRejected(error)) return;
  void endExpiredSession();
  return NEVER;
});
