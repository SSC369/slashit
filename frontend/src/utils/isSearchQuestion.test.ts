import { describe, expect, it } from "vitest";

import { isSearchQuestion } from "./isSearchQuestion";

describe("isSearchQuestion", () => {
  it.each([
    "when does my passport expire?",
    "passport?",
    "What is my blood type",
    "  does the dentist open saturday",
    "HAVE I paid rent",
  ])("reads %j as a question", (text) => {
    expect(isSearchQuestion(text)).toBe(true);
  });

  it.each(["passport", "whatever I saved about rent", "island trip", ""])(
    "reads %j as a word search",
    (text) => {
      expect(isSearchQuestion(text)).toBe(false);
    },
  );
});
