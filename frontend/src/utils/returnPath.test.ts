import { describe, expect, it } from "vitest";

import { buildSignInPath, readIsSessionExpired, readReturnPath } from "./returnPath";

describe("returnPath", () => {
  it("carries a deep link through sign-in and reads it back", () => {
    const signInPath = buildSignInPath("/records/reminders/r1?from=email");

    expect(signInPath).toBe("/sign-in?next=%2Frecords%2Freminders%2Fr1%3Ffrom%3Demail");
    expect(readReturnPath(signInPath.slice("/sign-in".length))).toBe(
      "/records/reminders/r1?from=email",
    );
  });

  it("sends home with no parameter", () => {
    expect(buildSignInPath("/")).toBe("/sign-in");
    expect(readReturnPath("")).toBe("/");
  });

  it.each(["//evil.example", "https://evil.example", "/\\evil.example", "records"])(
    "refuses %s as a return path, so it cannot redirect off the site",
    (unsafePath) => {
      expect(readReturnPath(`?next=${encodeURIComponent(unsafePath)}`)).toBe("/");
    },
  );

  it("002 FR-23: an expired session adds reason=expired beside the return path", () => {
    expect(buildSignInPath("/records", "EXPIRED")).toBe("/sign-in?next=%2Frecords&reason=expired");
    expect(buildSignInPath("/", "EXPIRED")).toBe("/sign-in?reason=expired");
    expect(buildSignInPath("/records", "USER")).toBe("/sign-in?next=%2Frecords");
    expect(readIsSessionExpired("?next=%2Frecords&reason=expired")).toBe(true);
    expect(readIsSessionExpired("?reason=other")).toBe(false);
  });
});
