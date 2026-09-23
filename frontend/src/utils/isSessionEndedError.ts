import { CombinedGraphQLErrors, ServerError } from "@apollo/client/errors";

/** The API's permission class answers a lapsed session with this message. */
const NOT_AUTHENTICATED_MESSAGE = "Not authenticated";

/** Whether a request failed because the session ended, rather than because
 * the network or the server did. The first is fixed by signing in again. */
export const isSessionEndedError = (error: unknown): boolean => {
  if (ServerError.is(error)) return error.statusCode === 401;
  if (CombinedGraphQLErrors.is(error)) {
    return error.errors.some((graphQLError) => graphQLError.message === NOT_AUTHENTICATED_MESSAGE);
  }
  return false;
};
