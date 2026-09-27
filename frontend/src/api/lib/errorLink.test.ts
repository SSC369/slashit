import { ApolloClient, ApolloLink, InMemoryCache, gql } from "@apollo/client";
import { Observable } from "rxjs";
import { afterEach, describe, expect, it, vi } from "vitest";

import { errorLink } from "./errorLink";

const mocks = vi.hoisted(() => ({ endExpiredSession: vi.fn() }));

vi.mock("./sessionExpiry", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./sessionExpiry")>()),
  endExpiredSession: () => mocks.endExpiredSession(),
}));

const QUERY = gql`
  query Probe {
    probe
  }
`;

const respondWith = (result: ApolloLink.Result): ApolloLink =>
  new ApolloLink(
    () =>
      new Observable((observer) => {
        observer.next(result);
        observer.complete();
      }),
  );

const run = (result: ApolloLink.Result): { next: ReturnType<typeof vi.fn> } => {
  const next = vi.fn();
  const client = new ApolloClient({
    cache: new InMemoryCache(),
    link: ApolloLink.empty(),
    defaultOptions: {
      watchQuery: { errorPolicy: "all" },
      query: { errorPolicy: "all" },
      mutate: { errorPolicy: "all" },
    },
  });
  ApolloLink.execute(
    ApolloLink.from([errorLink, respondWith(result)]),
    { query: QUERY },
    { client },
  ).subscribe({ next, error: vi.fn() });
  return { next };
};

describe("errorLink", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("002 T-4.3: an UNAUTHENTICATED refusal ends the session and draws nothing", () => {
    const { next } = run({
      data: null,
      errors: [
        {
          message: "Not authenticated",
          extensions: { code: "UNAUTHENTICATED" },
        },
      ],
    });

    expect(mocks.endExpiredSession).toHaveBeenCalledTimes(1);
    expect(next).not.toHaveBeenCalled();
  });

  it("002 T-4.3: any other error passes through and keeps the session", () => {
    const { next } = run({
      data: null,
      errors: [{ message: "Something else broke" }],
    });

    expect(mocks.endExpiredSession).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalledTimes(1);
  });

  it("002 T-4.3: a typed union error is data, not a refusal", () => {
    const { next } = run({ data: { probe: { __typename: "MemoryNotFound" } } });

    expect(mocks.endExpiredSession).not.toHaveBeenCalled();
    expect(next).toHaveBeenCalledTimes(1);
  });
});
